# About

This is a tool for easily scheduling and running python functions in a kubernetes cluster.
This is designed to be jupyter notebook friendly.

The project is still in early development.

# Dev Instructions

## Requirements
- docker
- minikube
- argo

```shell
minikube start
minikube mount $HOME/.pyflow:/.pyflow &
minikube dashboard
kubectl -n argo port-forward deployment/argo-server 2746:2746
```

## Test/Example

```python
python package.py
```
