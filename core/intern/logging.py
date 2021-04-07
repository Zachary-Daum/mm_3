from datetime import datetime

### Logging .LOG files ###
def write_log(loc,message,msg_type):
    with open(loc,'a') as f:
        f.write(datetime.now().strftime("%m-%d-%Y %H:%M:%S")+" "+msg_type+" "+str(message)+'\n')

class Logger():
    def __init__(self,name,log_file):
        self.name = name
        self.log_file = log_file

    def info(self,message):
        write_log(self.log_file,message,"INFO")

    def debug(self,message):
        write_log(self.log_file,message,"DEBUG")

    def warning(self,message):
        write_log(self.log_file,message,"WARNING")

    def error(self,message):
        write_log(self.log_file,message,"ERROR")

    def critical(self,message):
        write_log(self.log_file,message,"CRITICAL")

### Logging .JSON files ###
def write_data(loc,msg):
    with open(loc,'w') as f:
        f.write(str(msg) + '\n')

class data_log:
    def __init__(self,name,data_file):
        self.name = name
        self.data_file = data_file

    def log(self,message):
        write_data(self.data_file,message)