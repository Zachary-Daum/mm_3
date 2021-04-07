logs = ['./logs/agents.LOG','./logs/assets.LOG','./logs/books.LOG','./logs/market.LOG','./logs/model.LOG']

for log in logs:
    open(log,'w').close()