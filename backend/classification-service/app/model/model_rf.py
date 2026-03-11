import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ---------------------------------------------------
# Load cleaned datasets
# ---------------------------------------------------

train_df = pd.read_csv("training_dataset_clean.csv")
test_df = pd.read_csv("test_dataset_clean.csv")


# ---------------------------------------------------
# Prepare features and labels
# ---------------------------------------------------

X_train = train_df.drop(columns=["sha256", "label"])
y_train = train_df["label"]

X_test = test_df.drop(columns=["sha256", "label"])
y_test = test_df["label"]


# ---------------------------------------------------
# Train Random Forest model
# ---------------------------------------------------

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=30,
    max_features="sqrt",
    random_state=42,
    n_jobs=-1
)

print("Training model...")
model.fit(X_train, y_train)


# ---------------------------------------------------
# Save trained model
# ---------------------------------------------------

joblib.dump(model, "ransomware_rf_model.pkl")
print("Model saved as ransomware_rf_model.pkl")


# ---------------------------------------------------
# Predictions
# ---------------------------------------------------

y_pred = model.predict(X_test)


# ---------------------------------------------------
# Evaluation
# ---------------------------------------------------

print("\nAccuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))


# ---------------------------------------------------
# Feature importance
# ---------------------------------------------------

feature_importance = pd.Series(
    model.feature_importances_,
    index=X_train.columns
).sort_values(ascending=False)

print("\nTop 20 important trigrams:")
print(feature_importance.head(20))