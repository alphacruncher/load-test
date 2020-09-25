## Selenium on Kubernetes

Selenium is a browser automation tool used primarily for testing web applications. However when Selenium is used in a CI pipeline to test applications, there is often contention around the use of Selenium resources. This example shows you how to deploy Selenium to Kubernetes in a scalable fashion.

### Deploy Selenium Grid Hub:

We will be using Selenium Grid Hub to make our Selenium install scalable via a master/worker model. The Selenium Hub is the master, and the Selenium Nodes are the workers(not to be confused with Kubernetes nodes). We only need one hub, but we're using a replication controller to ensure that the hub is always running:

```console
kubectl create --filename=selenium-hub-deployment.yaml
```

The Selenium Nodes will need to know how to get to the Hub, let's create a service for the nodes to connect to.

```console
kubectl create --filename=selenium-hub-svc.yaml
```

### Verify Selenium Hub Deployment

Let's verify our deployment of Selenium hub by connecting to the web console.

Proxy via kubectl.

```console
export PODNAME=`kubectl get pods --selector="app=selenium-hub" --output=template --template="{{with index .items 0}}{{.metadata.name}}{{end}}"`
kubectl port-forward $PODNAME 4444:4444
```

In a separate terminal, you can now check the status.

```console
curl http://localhost:4444
```

### Deploy Firefox and Chrome Nodes:

Now that the Hub is up, we can deploy workers.

This will deploy 2 Chrome nodes.

```console
kubectl create --filename=selenium-node-chrome-deployment.yaml
```

And 2 Firefox nodes to match.

```console
kubectl create --filename=selenium-node-firefox-deployment.yaml
```

Once the pods start, you will see them show up in the Selenium Hub interface.

### Run a Selenium Job

Let's run a quick Selenium job to validate our setup.

#### Setup Python Environment

First, we need to start a python container that we can attach to. Make sure you are creating the pod in the selenium-loadtest namespace!

```console
kubectl run selenium-python --image=python:3.8.0 -- sleep 36000
```

Copy over the users.json and selenium test files:

```
kubectl cp selenium-test.py selenium-python:/tmp/
kubectl cp users.json selenium-python:/tmp/
```

Next, we need to get inside this container.

```console
export PODNAME=`kubectl get pods --selector="run=selenium-python" --output=template --template="{{with index .items 0}}{{.metadata.name}}{{end}}"`
kubectl exec --stdin=true --tty=true $PODNAME bash
```

Once inside, we need to install the Selenium library

```console
pip install selenium
```

Finally execute the tests:

```
cd /tmp
for i in {1..100}; do echo $i; sleep 3; nohup python selenium-test.py --userindex $i & done
```

### Scale your Firefox and Chrome nodes.

If you need more Firefox or Chrome nodes, your hardware is the limit:

```console
kubectl scale deployment selenium-node-firefox --replicas=10
kubectl scale deployment selenium-node-chrome --replicas=10
```

You now have 10 Firefox and 10 Chrome nodes, happy Seleniuming!

### Debugging

Sometimes it is necessary to check on a hung test. Each pod is running VNC. To check on one of the browser nodes via VNC, it's recommended that you proxy, since we don't want to expose a service for every pod, and the containers have a weak VNC password. Replace POD_NAME with the name of the pod you want to connect to.

```console
kubectl port-forward $POD_NAME 5900:5900
```

Then connect to localhost:5900 with your VNC client using the password "secret"

Enjoy your scalable Selenium Grid!

Adapted from: https://github.com/SeleniumHQ/docker-selenium

### Teardown

To remove all created resources, run the following:

```console
kubectl delete deployment selenium-hub
kubectl delete deployment selenium-node-chrome
kubectl delete deployment selenium-node-firefox
kubectl delete deployment selenium-python
kubectl delete svc selenium-hub
kubectl delete svc selenium-hub-external
```