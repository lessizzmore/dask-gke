# Train XGboost on A4 (B200s) GKE Node Pool

This recipe outlines the steps for running a XGBoost training workload on
[A4 GKE Node pools](https://cloud.google.com/kubernetes-engine).

## Orchestration and Deployment Tools

For this recipe, deploy A4 GKE Node Pool using [Cluster Toolkit](https://github.com/AI-Hypercomputer/gpu-recipes/blob/main/docs/configuring-environment-gke-a4.md)

## Build and Push Docker Image
```
# build and push docker image
## Define a variable for your image name to make it easy to reference
export IMAGE_NAME=""

## Build the image from the current directory
docker build -t $IMAGE_NAME .

## Push docker image to artifact registry
docker push $IMAGE_NAME
```
## Connect to GKE cluster
```
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

```
## Deploy Dask Scheduler and Workers
```
## In this example, both the dask scheduler and the 2 dask workers are deployed in the same a4 node pool.
## Each dask worker requests 8 B200 GPUs (1 A4 VM)
## To change the number of dask worker, change replicas: 2 as you need
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
