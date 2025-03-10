# main.py
from app import create_app
#from app.scheduler import scheduler

app = create_app()


if __name__ == '__main__':
    
    #print("Iniciando scheduler...")  # <--- Debug
    #with app.app_context():
    #    
    #    scheduler.start()
    #    print("Scheduler iniciado!")  # <--- Debug
    
    #app.run(debug=False, host='127.0.0.1', port=5000)
    app.run(debug=False, host='0.0.0.0', port=5000)
