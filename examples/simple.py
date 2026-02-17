import kiroframe_arcee as kiro

with kiro.init("test", "simple"):
    kiro.tag("key", "value")
    kiro.tag("test1", "test2")
    kiro.milestone("just a milestone")
    kiro.model("model_key", "/src/simple.py")
    kiro.model_version("1.23.45-rc")
    kiro.model_version_alias("winner")
    kiro.model_version_tag("key", "value")
    kiro.send({"t": 2})
    kiro.artifact(
        "https://s3/ml-bucket/artifacts/AccuracyChart.png",
        "Accuracy line chart",
        "The dependence of accuracy on the time",
        {"env": "staging"})
    kiro.artifact_tag("https://s3/ml-bucket/artifacts/AccuracyChart.png",
                      "key", "value")
print(kiro.info())
