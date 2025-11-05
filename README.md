# Train XGboost on A4 (B200s) GKE Node Pool

This recipe outlines the steps for running a XGBoost training workload on
[A4 GKE Node pools](https://cloud.google.com/kubernetes-engine).

## Deployment Overview
You have a persistent Dask cluster (scheduler and workers managed by Deployments) and a one-off task (data generation) managed by a Job. The Job leverages the Dask cluster to parallelize and accelerate the data generation process. 

- Scheduler Deployment:

This ensures that a Dask scheduler pod is always running and available. If the pod dies, Kubernetes will automatically create a new one.

- Worker Deployments:

Each Deployment manages a set of Dask worker pods. Like the scheduler, Deployments ensure that the desired number of worker pods are always running.

- Service:

The Service provides a stable network endpoint (a consistent IP address and DNS name) for the Dask scheduler. This is crucial because the scheduler's pod IP address can change if the pod is restarted. The workers use the Service's DNS name (e.g., dask-scheduler-svc) to discover and connect to the scheduler. This allows the workers to communicate with the scheduler regardless of which pod is currently running the scheduler process.

- Data Generation/Training Job:

The datagen.py script is executed as a Kubernetes Job. A Job creates one or more pods and ensures that a specified number of them successfully complete their tasks.In this case, the Job will run a pod that executes datagen.py. The datagen.py script connects to the Dask scheduler and submits tasks to the Dask cluster to generate the data. The Job pod acts as a client to the Dask cluster. It orchestrates the data generation process but doesn't directly perform the data generation itself. The actual data generation is distributed across the Dask workers. Once datagen.py completes its task (i.e., all data has been generated), the Job's pod will terminate, and the Job will be marked as completed.


## Orchestration and Deployment Tools

For this recipe, deploy A4 GKE Node Pool using [Cluster Toolkit](https://github.com/AI-Hypercomputer/gpu-recipes/blob/main/docs/configuring-environment-gke-a4.md)

## Build and Push Docker Image
```
## Define a variable for your image name to make it easy to reference
export IMAGE_NAME=""

## Build the image from the current directory
docker build -t $IMAGE_NAME .

## Push docker image to artifact registry
docker push $IMAGE_NAME
```

## Create GCS bucket for Data Generation

```
BUCKET_NAME="zt-dask-datagen"
REGION="US-CENTRAL1"
gcloud storage buckets create gs://${BUCKET_NAME} \
    --project=$(gcloud config get-value project) \
    --location=${REGION} \
    --storage-class=STANDARD
```

## Create k8s Service Account

```
kubectl create serviceaccount zt-fuse-ksa -n default
```

## Create the IAM Service Account (GSA) and Grant GCS Permissions

```
# Create the IAM Service Account (use the same name for clarity)
export PROJECT_ID=$(gcloud config get-value project)
export GSA_NAME="zt-fuse-gsa"

gcloud iam service-accounts create $GSA_NAME \
    --display-name "GCS FUSE Service Account"

# Grant the GSA the necessary Storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
   --member="serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
   --role="roles/storage.objectAdmin"
```

## Binds KSA to GSA (Workload Identity)

```
export K8S_SA_NAME="zt-fuse-ksa"
export NAMESPACE="default"

gcloud iam service-accounts add-iam-policy-binding \
    "${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/${K8S_SA_NAME}]"

kubectl annotate serviceaccount $K8S_SA_NAME -n $NAMESPACE \
    iam.gke.io/gcp-service-account="${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
```

## Connect to GKE cluster
```
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

```
## Deploy Dask Scheduler and Workers
In this example, both the dask scheduler and the 2 dask workers are deployed in the same a4 node pool. Dask scheduler and workers are connected using Service `dask-worker tcp://dask-scheduler-svc:8786`
Each dask worker requests 8 B200 GPUs (1 A4 VM).
To change the number of dask worker, change replicas: 2 as you need.

```
kubectl apply -f scheduler.yaml
kubectl apply -f worker.yaml
```
## Run Data Generation and Training Jobs
```
kubectl apply -f datagen.yaml
kubect apply -f training.yaml
```
## Monitor Job
```
kubectl get job
kubectl get pods --selector=job-name=scheduler-job
kubectl describe pod <scheduler-pod-name>

## check logs of finished container
kubectl logs <scheduler-pod-name> --container=scheduler --previous

## check dask dashboard
kubectl port-forward <scheduler-pod-name> 8787:8787
```
