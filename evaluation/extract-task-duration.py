import dateutil.parser
import pprint
import sys
from yaml import load_all

# 0. Load pod log
path = sys.argv[1]
mode = sys.argv[2]
pod_file = open(path)
data = load_all(pod_file)

task_durations = {
    "split": None,
    "chunk": None,
    "word-count": None,
    "sort": None,
    "merge": None,
    "calc": None,
}

pod_log = {}


def get_airflow_task_id(pod):
    task_id = pod["metadata"]["labels"]["task_id"]
    if "-aa" in task_id:
        task_id = task_id.split("-aa")[0]
    if "-ab" in task_id:
        task_id = task_id.split("-ab")[0]
    return task_id

def get_nextflow_task_id(pod):
    if not "taskName" in pod["metadata"]["labels"]:
        return None
    task_id = pod["metadata"]["labels"]["taskName"]
    if "word_count" in task_id:
        task_id = task_id.replace("word_", "word-")
    return task_id.split("_")[0]

def get_argo_task_id(pod):
    node_name = pod["metadata"]["annotations"]["workflows.argoproj.io/node-name"]
    task_id = node_name.split(".")[1]
    if "word-count" in task_id:
        return "word-count"
    else:
        return task_id.split("-")[0]

def get_snakemake_task_id(pod):
    command = pod["spec"]["containers"][0]["args"][1]
    args = command.split(" ")
    index = args.index("--allowed-rules")
    rule = args[index + 1]
    if rule == "count":
        return "word-count"
    return rule

def get_task_id(pod, mode):
    if mode == "airflow":
        return get_airflow_task_id(pod)
    elif mode == "argo":
        return get_argo_task_id(pod)
    elif mode == "nextflow":
        return get_nextflow_task_id(pod)
    elif mode == "snakemake":
        return get_snakemake_task_id(pod)
    raise Exception("Unknown mode")


def get_airflow_container(pod):
    return pod["status"]["containerStatuses"][0]

def get_argo_container(pod):
    for container in pod["status"]["containerStatuses"]:
        if "weislenn/utils" in container["image"]:
            return container
    return None

def get_nextflow_container(pod):
    return pod["status"]["containerStatuses"][0]

def get_snakemake_container(pod):
    return pod["status"]["containerStatuses"][0]

def get_container(pod, mode):
    if mode == "airflow":
        return get_airflow_container(pod)
    elif mode == "argo":
        return get_argo_container(pod)
    elif mode == "nextflow":
        return get_nextflow_container(pod)
    elif mode == "snakemake":
        return get_snakemake_container(pod)
    raise Exception("Unknown mode")


# 1. Extract pod info from file and calculate durations
for pod in data:
    name = pod["metadata"]["name"]
    task_id = get_task_id(pod, mode)
    if not task_id:
        continue
    if not "containerStatuses" in pod["status"]:
        continue
    container = get_container(pod, mode)
    if not container:
        continue
    container_status = container["state"]
    if not "terminated" in container_status:
        continue

    if not name in pod_log:
        start_time = dateutil.parser.isoparse(
            container_status["terminated"]["startedAt"])
        end_time = dateutil.parser.isoparse(
            container_status["terminated"]["finishedAt"])
        pod_log[name] = {
            "task_id": task_id,
            "duration": (end_time - start_time).total_seconds(),
        }
pod_file.close()

# 2. Collect and compare duration data
for pod in pod_log.values():
    if not task_durations[pod["task_id"]]:
        task_durations[pod["task_id"]] = {
            "min": pod["duration"],
            "max": pod["duration"],
            "duration_list": [pod["duration"]],
            "pod_count": 1
        }
    else:
        if pod["duration"] < task_durations[pod["task_id"]]["min"]:
            task_durations[pod["task_id"]]["min"] = pod["duration"]
        if pod["duration"] > task_durations[pod["task_id"]]["max"]:
            task_durations[pod["task_id"]]["max"] = pod["duration"]
        task_durations[pod["task_id"]]["pod_count"] += 1
        task_durations[pod["task_id"]]["duration_list"].append(pod["duration"])

# 3. Compute average
for task_id in task_durations:
    total_length = sum(task_durations[task_id]["duration_list"])
    avg = total_length / task_durations[task_id]["pod_count"]
    task_durations[task_id]["average"] = avg
    del(task_durations[task_id]["duration_list"])


pp = pprint.PrettyPrinter(depth=5)
pp.pprint(task_durations)
