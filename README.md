- https://www.geeksforgeeks.org/python-decorators-a-complete-guide/?ref=ml_lbp
- https://docs.anaconda.com/free/anaconda/applications/docker/
- https://stackoverflow.com/questions/30469575/how-to-pickle-and-unpickle-to-portable-string-in-python-3
- https://stackoverflow.com/questions/15200048/how-to-get-the-parameters-type-and-return-type-of-a-function
- https://minikube.sigs.k8s.io/docs/start/
- https://argoproj.github.io/argo-workflows/quick-start/
- https://stackoverflow.com/questions/48534980/mount-local-directory-into-pod-in-minikube
- https://thospfuller.com/2020/12/09/learn-how-to-mount-a-local-drive-in-a-pod-in-minikube-2021/
- https://stackoverflow.com/questions/42564058/how-to-use-local-docker-images-with-minikube
- https://minikube.sigs.k8s.io/docs/handbook/pushing/#1-pushing-directly-to-the-in-cluster-docker-daemon-docker-env

# Instructions

```shell
minikube start
minikube mount $HOME/.pyflow:/.pyflow &
minikube dashboard
kubectl -n argo port-forward deployment/argo-server 2746:2746
```

```python
docker build . -t conda
docker run -it -v $HOME/.pyflow:/root/.pyflow conda bash
docker run -it -v $HOME/.pyflow:/root/.pyflow pyflow_test_fn:1 python -c "from pyflow.pyflow import Pyflow; Pyflow().fn('step2')('Hello World')"
```

# Details


The benefit of this style is that you can register the functions without executing them.
The issue with this is that pickling the function is not very human readable. To establish provenance,
you would need to store the function itself.  You could also store
the function name and the arguments that were passed to it, but this is not very robust.  You could
also store the function name and the hash of the function, but this is not very human readable either.

Another problem here is that when you call a function, there is no autocomplete for the arguments.
So you have to know what the arguments are before you call the function. This is not very user friendly.

Another problem with he pickle approach is that you don't know the output format. Making it hard to pass
variables along.  You could store the output format in the metadata, but this is not very robust.

Another problem is that not all code can be pickled. You might run into an issue where you cannot use it.

Optional: Use init script to install all the requirements and then run the function
This means you can reuse a container for multiple runs, but will you have
access to all the repos...tbd. But the run will not be reproducible
because the container will be updated with the latest packages.
