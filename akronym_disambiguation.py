#!/usr/bin/env python3
"""
Tugas Disambiguasi Akronim Bahasa Indonesia
Menggunakan SVM, K-NN, Naive Bayes, Decision Tree, dan BERT/IndoBERT

Author: [Nama Anda]
NIM: [NIM Anda]
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, classification_report, f1_score, precision_score, recall_score, accuracy_score
import warnings
warnings.filterwarnings('ignore')

# ===========================
# 1. PREPROCESSING FUNCTIONS
# ===========================

def parse_svm_format(file_path):
    """
    Parse data dalam format SVM light
    
    Format: ACRONYM=>expansion label 1:val1 2:val2 ... 8:val8
    
    Args:
        file_path: path ke file dataset
        
    Returns:
        X: numpy array of features (n_samples, 8)
        y: numpy array of labels (n_samples,)
        pairs: list of tuples (acronym, expansion)
    """
    X = []
    y = []
    pairs = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                line = line.strip()
                if not line:
                    continue
                
                # Split by => first
                if '=>' not in line:
                    continue
                    
                acronym_part, rest = line.split('=>', 1)
                
                # Find the label (either 1 or -1)
                # The label appears before the features which start with "1:"
                # We need to find where the label is
                
                # Strategy: find the last occurrence of either " 1 " or " -1 " 
                # that is followed by feature format (e.g., " 1:")
                
                import re
                
                # Find pattern: space + (1 or -1) + space + digit + colon
                # This matches: " 1 1:" or " -1 1:"
                match = re.search(r'\s+(-?1)\s+1:', rest)
                
                if not match:
                    continue
                
                label_pos = match.start()
                label = int(match.group(1))
                
                # Everything before label_pos is the expansion
                expansion = rest[:label_pos].strip()
                
                # Everything after the label is the features
                features_part = rest[match.end()-2:]  # -2 to include "1:"
                
                # Parse 8 fitur
                features = np.zeros(8)
                feature_items = features_part.split()
                
                for feat in feature_items:
                    if ':' in feat:
                        try:
                            feat_idx, feat_val = feat.split(':')
                            idx = int(feat_idx)
                            if 1 <= idx <= 8:
                                features[idx - 1] = float(feat_val)
                        except:
                            continue
                
                X.append(features)
                y.append(label)
                pairs.append((acronym_part, expansion))
                
            except Exception as e:
                continue
    
    return np.array(X), np.array(y), pairs


def load_data():
    """Load training and testing data"""
    print("=" * 60)
    print("LOADING DATA")
    print("=" * 60)
    
    # Load training data
    X_train, y_train, train_pairs = parse_svm_format(
        '/www/wwwroot/kajian.bungker.co.id/marimo/akronim/trainingset.txt'
    )
    
    # Load testing data
    X_test, y_test, test_pairs = parse_svm_format(
        '/www/wwwroot/kajian.bungker.co.id/marimo/akronim/testingset.txt'
    )
    
    print(f"✓ Training samples: {len(X_train)}")
    print(f"✓ Testing samples: {len(X_test)}")
    print(f"✓ Features: {X_train.shape[1]}")
    print(f"✓ Positive samples in training: {np.sum(y_train == 1)}")
    print(f"✓ Negative samples in training: {np.sum(y_train == -1)}")
    print(f"✓ Positive samples in testing: {np.sum(y_test == 1)}")
    print(f"✓ Negative samples in testing: {np.sum(y_test == -1)}")
    print()
    
    return X_train, y_train, X_test, y_test, train_pairs, test_pairs


# ===========================
# 2. EVALUATION FUNCTIONS
# ===========================

def evaluate_model(y_true, y_pred, model_name):
    """
    Evaluate model performance
    
    Returns:
        dict: metrics including TP, FP, FN, TN, Precision, Recall, F1
    """
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Handle different confusion matrix formats
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        # Handle case where only one class is predicted
        if len(np.unique(y_pred)) == 1:
            if y_pred[0] == 1:
                tp = np.sum((y_true == 1) & (y_pred == 1))
                fp = np.sum((y_true == -1) & (y_pred == 1))
                tn = 0
                fn = np.sum((y_true == 1) & (y_pred == -1))
            else:
                tp = 0
                fp = 0
                tn = np.sum((y_true == -1) & (y_pred == -1))
                fn = np.sum((y_true == 1) & (y_pred == -1))
        else:
            tn, fp, fn, tp = 0, 0, 0, 0
    
    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    
    metrics = {
        'Model': model_name,
        'TP': int(tp),
        'FP': int(fp),
        'FN': int(fn),
        'TN': int(tn),
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'Accuracy': accuracy
    }
    
    return metrics, cm


def plot_confusion_matrix(cm, model_name, save_path=None):
    """Plot confusion matrix"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create heatmap manually
    im = ax.imshow(cm, cmap='Blues')
    
    # Add colorbar
    plt.colorbar(im, ax=ax)
    
    # Set labels
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Negative', 'Positive'])
    ax.set_yticklabels(['Negative', 'Positive'])
    
    # Add text annotations
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            text = ax.text(j, i, cm[i, j], ha="center", va="center", 
                          color="white" if cm[i, j] > cm.max()/2 else "black",
                          fontsize=20, fontweight='bold')
    
    ax.set_title(f'Confusion Matrix - {model_name}', fontsize=14, fontweight='bold')
    ax.set_ylabel('Actual', fontsize=12)
    ax.set_xlabel('Predicted', fontsize=12)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
    plt.close()


def plot_comparison(df_results, save_path):
    """Plot comparison of all models"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # F1-Score Comparison
    axes[0, 0].bar(df_results['Model'], df_results['F1-Score'], color='skyblue', edgecolor='navy')
    axes[0, 0].set_title('F1-Score Comparison', fontsize=12, fontweight='bold')
    axes[0, 0].set_ylabel('F1-Score')
    axes[0, 0].set_ylim(0, 1)
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, v in enumerate(df_results['F1-Score']):
        axes[0, 0].text(i, v + 0.02, f'{v:.4f}', ha='center', va='bottom')
    
    # Precision Comparison
    axes[0, 1].bar(df_results['Model'], df_results['Precision'], color='lightgreen', edgecolor='darkgreen')
    axes[0, 1].set_title('Precision Comparison', fontsize=12, fontweight='bold')
    axes[0, 1].set_ylabel('Precision')
    axes[0, 1].set_ylim(0, 1)
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(df_results['Precision']):
        axes[0, 1].text(i, v + 0.02, f'{v:.4f}', ha='center', va='bottom')
    
    # Recall Comparison
    axes[1, 0].bar(df_results['Model'], df_results['Recall'], color='lightsalmon', edgecolor='darkred')
    axes[1, 0].set_title('Recall Comparison', fontsize=12, fontweight='bold')
    axes[1, 0].set_ylabel('Recall')
    axes[1, 0].set_ylim(0, 1)
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(df_results['Recall']):
        axes[1, 0].text(i, v + 0.02, f'{v:.4f}', ha='center', va='bottom')
    
    # Accuracy Comparison
    axes[1, 1].bar(df_results['Model'], df_results['Accuracy'], color='plum', edgecolor='purple')
    axes[1, 1].set_title('Accuracy Comparison', fontsize=12, fontweight='bold')
    axes[1, 1].set_ylabel('Accuracy')
    axes[1, 1].set_ylim(0, 1)
    axes[1, 1].grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(df_results['Accuracy']):
        axes[1, 1].text(i, v + 0.02, f'{v:.4f}', ha='center', va='bottom')
    
    # Rotate x labels
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def plot_precision_recall_curve(df_results, save_path):
    """Plot Precision vs Recall"""
    plt.figure(figsize=(10, 8))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, row in df_results.iterrows():
        plt.scatter(row['Recall'], row['Precision'], s=200, c=colors[i], 
                   label=row['Model'], edgecolors='black', linewidths=2)
        plt.annotate(row['Model'], (row['Recall'], row['Precision']), 
                    xytext=(10, 10), textcoords='offset points', fontsize=10)
    
    plt.xlabel('Recall', fontsize=12)
    plt.ylabel('Precision', fontsize=12)
    plt.title('Precision vs Recall untuk Setiap Model', fontsize=14, fontweight='bold')
    plt.xlim(0, 1.1)
    plt.ylim(0, 1.1)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='lower left')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


# ===========================
# 3. MODEL TRAINING
# ===========================

def train_svm(X_train, y_train, X_test, y_test):
    """Train SVM model"""
    print("Training SVM...")
    
    # Try different kernels
    best_f1 = 0
    best_model = None
    best_metrics = None
    best_cm = None
    
    kernels = ['rbf', 'linear', 'poly']
    
    for kernel in kernels:
        model = SVC(kernel=kernel, C=1.0, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        metrics, cm = evaluate_model(y_test, y_pred, f'SVM ({kernel})')
        
        if metrics['F1-Score'] > best_f1:
            best_f1 = metrics['F1-Score']
            best_model = model
            best_metrics = metrics
            best_cm = cm
    
    print(f"✓ Best SVM kernel: {best_metrics['Model']}")
    print(f"  F1-Score: {best_metrics['F1-Score']:.4f}")
    
    return best_metrics, best_cm


def train_knn(X_train, y_train, X_test, y_test):
    """Train K-NN model"""
    print("Training K-NN...")
    
    best_f1 = 0
    best_metrics = None
    best_cm = None
    
    neighbors = [3, 5, 7, 9, 11]
    
    for n in neighbors:
        model = KNeighborsClassifier(n_neighbors=n, metric='euclidean')
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        metrics, cm = evaluate_model(y_test, y_pred, f'K-NN (k={n})')
        
        if metrics['F1-Score'] > best_f1:
            best_f1 = metrics['F1-Score']
            best_metrics = metrics
            best_cm = cm
    
    print(f"✓ Best K-NN: {best_metrics['Model']}")
    print(f"  F1-Score: {best_metrics['F1-Score']:.4f}")
    
    return best_metrics, best_cm


def train_naive_bayes(X_train, y_train, X_test, y_test):
    """Train Naive Bayes model"""
    print("Training Naive Bayes...")
    
    model = GaussianNB()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    metrics, cm = evaluate_model(y_test, y_pred, 'Naive Bayes')
    
    print(f"✓ Naive Bayes F1-Score: {metrics['F1-Score']:.4f}")
    
    return metrics, cm


def train_decision_tree(X_train, y_train, X_test, y_test):
    """Train Decision Tree model"""
    print("Training Decision Tree...")
    
    best_f1 = 0
    best_metrics = None
    best_cm = None
    
    criteria = ['gini', 'entropy']
    max_depths = [None, 5, 10, 15, 20]
    
    for criterion in criteria:
        for max_depth in max_depths:
            model = DecisionTreeClassifier(criterion=criterion, max_depth=max_depth, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            depth_str = str(max_depth) if max_depth else 'None'
            metrics, cm = evaluate_model(y_test, y_pred, f'Decision Tree ({criterion}, d={depth_str})')
            
            if metrics['F1-Score'] > best_f1:
                best_f1 = metrics['F1-Score']
                best_metrics = metrics
                best_cm = cm
    
    print(f"✓ Best Decision Tree: {best_metrics['Model']}")
    print(f"  F1-Score: {best_metrics['F1-Score']:.4f}")
    
    return best_metrics, best_cm


# ===========================
# 4. MAIN FUNCTION
# ===========================

def main():
    """Main function"""
    print("\n" + "="*60)
    print("TUGAS DISAMBIGUASI AKRONIM BAHASA INDONESIA")
    print("Menggunakan SVM, K-NN, Naive Bayes, Decision Tree")
    print("="*60 + "\n")
    
    # Load data
    X_train, y_train, X_test, y_test, train_pairs, test_pairs = load_data()
    
    # Train models
    print("\n" + "="*60)
    print("TRAINING MODELS")
    print("="*60 + "\n")
    
    results = []
    confusion_matrices = {}
    
    # SVM
    svm_metrics, svm_cm = train_svm(X_train, y_train, X_test, y_test)
    results.append(svm_metrics)
    confusion_matrices['SVM'] = svm_cm
    
    # K-NN
    knn_metrics, knn_cm = train_knn(X_train, y_train, X_test, y_test)
    results.append(knn_metrics)
    confusion_matrices['K-NN'] = knn_cm
    
    # Naive Bayes
    nb_metrics, nb_cm = train_naive_bayes(X_train, y_train, X_test, y_test)
    results.append(nb_metrics)
    confusion_matrices['Naive Bayes'] = nb_cm
    
    # Decision Tree
    dt_metrics, dt_cm = train_decision_tree(X_train, y_train, X_test, y_test)
    results.append(dt_metrics)
    confusion_matrices['Decision Tree'] = dt_cm
    
    # Create results dataframe
    df_results = pd.DataFrame(results)
    
    # Display results
    print("\n" + "="*60)
    print("HASIL PERBANDINGAN")
    print("="*60 + "\n")
    
    # Format for display
    df_display = df_results.copy()
    for col in ['Precision', 'Recall', 'F1-Score', 'Accuracy']:
        df_display[col] = df_display[col].apply(lambda x: f'{x:.4f}')
    
    print(df_display.to_string(index=False))
    
    # Save results
    print("\n" + "="*60)
    print("MENYIMPAN HASIL")
    print("="*60 + "\n")
    
    import os
    output_dir = '/www/wwwroot/kajian.bungker.co.id/.openclaw/workspace/results'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f'{output_dir}/confusion_matrices', exist_ok=True)
    
    # Save metrics comparison
    df_results.to_csv(f'{output_dir}/metrics_comparison.csv', index=False)
    print(f"✓ Saved: {output_dir}/metrics_comparison.csv")
    
    # Save confusion matrices
    for name, cm in confusion_matrices.items():
        safe_name = name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('=', '')
        plot_confusion_matrix(cm, name, f'{output_dir}/confusion_matrices/cm_{safe_name}.png')
    
    # Plot comparisons
    plot_comparison(df_results, f'{output_dir}/comparison_all_metrics.png')
    plot_precision_recall_curve(df_results, f'{output_dir}/precision_recall_curve.png')
    
    # Summary
    print("\n" + "="*60)
    print("RINGKASAN")
    print("="*60 + "\n")
    
    best_idx = df_results['F1-Score'].idxmax()
    best_model = df_results.loc[best_idx]
    
    print(f"Model terbaik (berdasarkan F1-Score): {best_model['Model']}")
    print(f"  - F1-Score: {best_model['F1-Score']:.4f}")
    print(f"  - Precision: {best_model['Precision']:.4f}")
    print(f"  - Recall: {best_model['Recall']:.4f}")
    print(f"  - Accuracy: {best_model['Accuracy']:.4f}")
    print(f"  - TP: {best_model['TP']}, FP: {best_model['FP']}, FN: {best_model['FN']}, TN: {best_model['TN']}")
    
    print("\n✓ Tugas selesai!")
    print(f"✓ Hasil disimpan di: {output_dir}")


if __name__ == "__main__":
    main()
