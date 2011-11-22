
from glimpse.executors.cluster_executor import ClusterExecutor
from glimpse.executors.executor import StaticMap
from glimpse.util.zmq_cluster import Connect, Worker
import logging
import threading
import multiprocessing
import time
import unittest
import zmq

def WorkerProcessTarget(request_receiver, result_sender, callback,
    command_receiver):
  context = zmq.Context()
  worker = Worker(context, request_receiver, result_sender, callback,
      command_receiver)
  worker.Setup()
  worker.Run()

class TestClusterExecutor_Multicore(unittest.TestCase):

  def test_quitsOnCommand(self):
    use_threading = False
    callback = lambda x: x * 100
    context = zmq.Context()
    # bind the command_sender socket
    command_sender = Connect(url = "ipc://commands.ipc", bind = True)
    # launch the cluster executor
    #   request_sender and result_receiver bind
    #   command_receiver connects
    request_sender = Connect("ipc://requests.ipc", bind = True)
    result_receiver = Connect("ipc://results.ipc", bind = True)
    command_receiver = Connect("ipc://commands.ipc",
        options = {zmq.SUBSCRIBE : ""})  # subscribe to all command messages
    executor = ClusterExecutor(context, request_sender, result_receiver,
        command_sender, command_receiver, use_threading = use_threading)
    executor.Setup()
    time.sleep(1)
    # launch the worker
    #   all sockets connect
    request_receiver = Connect("ipc://requests.ipc")
    result_sender = Connect("ipc://results.ipc")
    worker = multiprocessing.Process(target = WorkerProcessTarget, args = (
        request_receiver, result_sender, callback, command_receiver))
    worker.daemon = True
    worker.start()
    # tear down the worker
    Worker.SendKillCommand(context, command_sender)
    worker.join(100)
    self.assertFalse(worker.is_alive())
    # tear down the cluster executor
    executor.Shutdown()
    self.assertFalse(executor.sink.is_alive())

  # test that basic Put()/Get() call pair works
  def test_putGet(self):
    use_threading = False
    callback = lambda x: x * 100
    context = zmq.Context()
    # bind the command_sender socket
    command_sender = Connect(url = "ipc://commands.ipc", bind = True)
    # launch the cluster executor
    #   request_sender and result_receiver bind
    #   command_receiver connects
    request_sender = Connect("ipc://requests.ipc", bind = True)
    result_receiver = Connect("ipc://results.ipc", bind = True)
    command_receiver = Connect("ipc://commands.ipc",
        options = {zmq.SUBSCRIBE : ""})  # subscribe to all command messages
    executor = ClusterExecutor(context, request_sender, result_receiver,
        command_sender, command_receiver, use_threading = use_threading)
    executor.Setup()
    time.sleep(1)
    # launch the worker
    #   all sockets connect
    request_receiver = Connect("ipc://requests.ipc")
    result_sender = Connect("ipc://results.ipc")
    worker = multiprocessing.Process(target = WorkerProcessTarget, args = (
        request_receiver, result_sender, callback, command_receiver))
    worker.daemon = True
    worker.start()
    executor.Put(2)
    self.assertEqual(200, executor.Get())
    # tear down the worker
    Worker.SendKillCommand(context, command_sender)
    worker.join(100)
    self.assertFalse(worker.is_alive())
    # tear down the cluster executor
    executor.Shutdown()
    self.assertFalse(executor.sink.is_alive())

  # test that map works
  def test_map(self):
    use_threading = True
    callback = lambda x: x * 100
    context = zmq.Context()
    # bind the command_sender socket
    command_sender = Connect(url = "ipc://commands.ipc", bind = True)
    # launch the cluster executor
    #   request_sender and result_receiver bind
    #   command_receiver connects
    request_sender = Connect("ipc://requests.ipc", bind = True)
    result_receiver = Connect("ipc://results.ipc", bind = True)
    command_receiver = Connect("ipc://commands.ipc",
        options = {zmq.SUBSCRIBE : ""})  # subscribe to all command messages
    executor = ClusterExecutor(context, request_sender, result_receiver,
        command_sender, command_receiver, use_threading = use_threading)
    executor.Setup()
    time.sleep(1)
    # launch the worker
    #   all sockets connect
    request_receiver = Connect("ipc://requests.ipc")
    result_sender = Connect("ipc://results.ipc")
    worker = multiprocessing.Process(target = WorkerProcessTarget, args = (
        request_receiver, result_sender, callback, command_receiver))
    worker.daemon = True
    worker.start()
    xs = range(10)
    expected = map(callback, xs)
    actual = sorted(StaticMap(executor, xs))
    self.assertEqual(expected, actual)
    # tear down the worker
    Worker.SendKillCommand(context, command_sender)
    worker.join(100)
    self.assertFalse(worker.is_alive())
    # tear down the cluster executor
    executor.Shutdown()
    self.assertFalse(executor.sink.is_alive())

def WorkerThreadTarget(context, request_receiver, result_sender, callback,
    command_receiver):
  worker = Worker(context, request_receiver, result_sender, callback,
      command_receiver)
  worker.Setup()
  worker.Run()

class TestClusterExecutor_Threaded(unittest.TestCase):

  def test_quitsOnCommand(self):
    use_threading = True
    callback = lambda x: x * 100
    context = zmq.Context()
    # bind the command_sender socket
    command_sender = context.socket(zmq.PUB)
    command_sender.bind("inproc://commands")
    # launch the cluster executor
    #   request_sender and result_receiver bind
    #   command_receiver connects
    request_sender = Connect("inproc://requests", bind = True)
    result_receiver = Connect("inproc://results", bind = True)
    command_receiver = Connect("inproc://commands",
        options = {zmq.SUBSCRIBE : ""})  # subscribe to all command messages
    executor = ClusterExecutor(context, request_sender, result_receiver,
        command_sender, command_receiver, use_threading = use_threading)
    executor.Setup()
    time.sleep(1)
    # launch the worker
    #   all sockets connect
    request_receiver = Connect("inproc://requests")
    result_sender = Connect("inproc://results")
    worker = threading.Thread(target = WorkerThreadTarget, args = (context,
        request_receiver, result_sender, callback, command_receiver))
    worker.daemon = True
    worker.start()
    # tear down the worker
    Worker.SendKillCommand(context, command_sender)
    worker.join(100)
    self.assertFalse(worker.is_alive())
    # tear down the cluster executor
    executor.Shutdown()
    self.assertFalse(executor.sink.is_alive())

  # test that basic Put()/Get() call pair works
  def test_putGet(self):
    use_threading = True
    callback = lambda x: x * 100
    context = zmq.Context()
    # bind the command_sender socket
    command_sender = context.socket(zmq.PUB)
    command_sender.bind("inproc://commands")
    # launch the cluster executor
    #   request_sender and result_receiver bind
    #   command_receiver connects
    request_sender = Connect("inproc://requests", bind = True)
    result_receiver = Connect("inproc://results", bind = True)
    command_receiver = Connect("inproc://commands",
        options = {zmq.SUBSCRIBE : ""})  # subscribe to all command messages
    executor = ClusterExecutor(context, request_sender, result_receiver,
        command_sender, command_receiver, use_threading = use_threading)
    executor.Setup()
    time.sleep(1)
    # launch the worker
    #   all sockets connect
    request_receiver = Connect("inproc://requests")
    result_sender = Connect("inproc://results")
    worker = threading.Thread(target = WorkerThreadTarget, args = (context,
        request_receiver, result_sender, callback, command_receiver))
    worker.daemon = True
    worker.start()
    executor.Put(2)
    self.assertEqual(200, executor.Get())
    # tear down the worker
    Worker.SendKillCommand(context, command_sender)
    worker.join(100)
    self.assertFalse(worker.is_alive())
    # tear down the cluster executor
    executor.Shutdown()
    self.assertFalse(executor.sink.is_alive())

  # test that map works
  def test_map(self):
    use_threading = True
    callback = lambda x: x * 100
    context = zmq.Context()
    # bind the command_sender socket
    command_sender = context.socket(zmq.PUB)
    command_sender.bind("inproc://commands")
    # launch the cluster executor
    #   request_sender and result_receiver bind
    #   command_receiver connects
    request_sender = Connect("inproc://requests", bind = True)
    result_receiver = Connect("inproc://results", bind = True)
    command_receiver = Connect("inproc://commands",
        options = {zmq.SUBSCRIBE : ""})  # subscribe to all command messages
    executor = ClusterExecutor(context, request_sender, result_receiver,
        command_sender, command_receiver, use_threading = use_threading)
    executor.Setup()
    time.sleep(1)
    # launch the worker
    #   all sockets connect
    request_receiver = Connect("inproc://requests")
    result_sender = Connect("inproc://results")
    worker = threading.Thread(target = WorkerThreadTarget, args = (context,
        request_receiver, result_sender, callback, command_receiver))
    worker.daemon = True
    worker.start()
    xs = range(10)
    expected = map(callback, xs)
    actual = sorted(StaticMap(executor, xs))
    self.assertEqual(expected, actual)
    # tear down the worker
    Worker.SendKillCommand(context, command_sender)
    worker.join(100)
    self.assertFalse(worker.is_alive())
    # tear down the cluster executor
    executor.Shutdown()
    self.assertFalse(executor.sink.is_alive())

if __name__ == '__main__':

  # Uncomment the following for debugging messages.
  #logging.getLogger().setLevel(logging.INFO)

  # Uncomment the following to run a subset of tests.
  #~ suite = unittest.TestLoader().loadTestsFromTestCase(
      #~ TestClusterExecutor_Multicore)
  #~ unittest.TextTestRunner(verbosity=2).run(suite)

  unittest.main()
