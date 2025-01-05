class Signal:
    def __init__(self):
        self.receivers=[]

    def connect(self,receiver):
        if receiver not in self.receivers:
            self.receivers.append(receiver)
            print(f"Connected receiver: {receiver}")
    
    def disconnect(self,receiver):
        if receiver in self.receivers:
            self.receivers.remove(receiver)
            print(f"Disconnected receiver: {receiver}")

    def send(self,**named):
        responses =[]
        for receiver in self.receivers:
            try:
                response =receiver(signal=self,**named)    
                responses.append((receiver,response))
                print("Successfully sent the notification")
            except Exception as e:
                print(f"Error in receiver {receiver}:{e}")
                break
        return responses