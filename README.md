# Instructions

```shell
minikube start
minikube mount $HOME/.pyflow:/.pyflow &
minikube dashboard
kubectl -n argo port-forward deployment/argo-server 2746:2746
```

```python
python package.py
```
