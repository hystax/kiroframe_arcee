from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

iris = load_iris()
X, y = iris.data, iris.target
feature_names = iris.feature_names
target_names = iris.target_names

print("Shape:", X.shape)
print("Classes:", target_names)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

y_pred = rf_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
step = 11
print("step:", step)
print("Classification report:")
report = classification_report(y_test, y_pred, target_names=target_names)
print(report)

with open('iris.txt', 'w') as f:
    f.write(report)

# prediction
new_sample = [[5.1, 3.5, 1.4, 0.2]]
prediction = rf_model.predict(new_sample)
print(f"\nprediction: {target_names[prediction[0]]}")
