from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
#from airflow.operators.bash import BashOperator
from kubernetes.client import models as k8s

volume_mount = k8s.V1VolumeMount(name='input', mount_path='/mount')
volume = k8s.V1Volume(
    name='input',
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
        claim_name='input'))

# This is number of lines of input / 2 / chunk_size
CHUNK_COUNT = 2

dag = DAG(
    'word-count',
    max_active_tasks=100,
    schedule_interval='@once',
    start_date=datetime(2021, 1, 1))

split_task = KubernetesPodOperator(
    dag=dag,
    name='split',
    image="weislenn/utils",
    image_pull_policy="Always",
    task_id='split',
    cmds=['bash', '-c', 'split.sh /mount/data/input.txt && mv chunk_a* /mount'],
    volumes=[volume],
    volume_mounts=[volume_mount],
    in_cluster=False,
    is_delete_operator_pod=True,
    namespace="airflow")

chunk_operators = {}
wc_operators = {}
sort_operators = {}
merge_operators = {}
PARTS = ['aa', 'ab']
for part in PARTS:
    wc_operators[part] = {}
    sort_operators[part] = {}
    chunk_operators[part] = KubernetesPodOperator(
        dag=dag,
        name='chunk-{}'.format(part),
        image="weislenn/utils",
        image_pull_policy="Always",
        task_id='chunk-{}'.format(part),
        cmds=['bash', '-c', 'cd /mount/ && split chunk_{} -d -l 2 -a 4 input_{}_'.format(
            part, part)],
        volumes=[volume],
        volume_mounts=[volume_mount],
        in_cluster=False,
        is_delete_operator_pod=True,
        namespace="airflow")

    for i in range(CHUNK_COUNT):
        chunk_id = str(i).zfill(4)
        wc_operators[part][i] = KubernetesPodOperator(
            dag=dag,
            name='word-count-{}-{}'.format(part, i),
            image="weislenn/utils",
            image_pull_policy="Always",
            task_id='word-count-{}-{}'.format(part, i),
            cmds=['bash', '-c', 'word_count.py /mount/input_{}_{} > /mount/count_{}_{}'.format(
                part, chunk_id, part, chunk_id)],
            volumes=[volume],
            volume_mounts=[volume_mount],
            in_cluster=False,
            is_delete_operator_pod=True,
            namespace="airflow")

        sort_operators[part][i] = KubernetesPodOperator(
            dag=dag,
            name='sort-{}-{}'.format(part, i),
            image="weislenn/utils",
            image_pull_policy="Always",
            task_id='sort-{}-{}'.format(part, i),
            cmds=['bash', '-c', 'sort.py /mount/count_{}_{} > /mount/sort_{}_{}'.format(
                part, chunk_id, part, chunk_id)],
            volumes=[volume],
            volume_mounts=[volume_mount],
            in_cluster=False,
            is_delete_operator_pod=True,
            namespace="airflow")

    merge_operators[part] = KubernetesPodOperator(
        dag=dag,
        name='merge-{}'.format(part),
        image="weislenn/utils",
        image_pull_policy="Always",
        task_id='merge-{}'.format(part),
        cmds=['bash', '-c', 'merge2.py /mount/sort_{}_ > /mount/merged_{}'.format(part, part)],
        volumes=[volume],
        volume_mounts=[volume_mount],
        in_cluster=False,
        is_delete_operator_pod=True,
        namespace="airflow")

calc_task = KubernetesPodOperator(
    dag=dag,
    name='calc',
    image="weislenn/utils",
    image_pull_policy="Always",
    task_id='calc',
    cmds=['bash', '-c', 'calc_deviance.py /mount/merged_aa /mount/merged_ab'],
    volumes=[volume],
    volume_mounts=[volume_mount],
    in_cluster=False,
    is_delete_operator_pod=True,
    namespace="airflow")

for part in PARTS:
    split_task >> chunk_operators[part]
    for i in range(CHUNK_COUNT):
        chunk_operators[part] >> wc_operators[part][i]
        wc_operators[part][i] >> sort_operators[part][i]
        sort_operators[part][i] >> merge_operators[part]
    merge_operators[part] >> calc_task
