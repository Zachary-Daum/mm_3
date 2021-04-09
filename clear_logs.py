logs = ['./logs/agents.LOG','./logs/assets.LOG','./logs/books.LOG','./logs/market.LOG','./logs/model.LOG']


def clr_logs():
    for log in logs:
        open(log,'w').close()


if __name__ == "__main__":
    clr_logs()