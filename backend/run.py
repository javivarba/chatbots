﻿from app import create_app

app = create_app('default')

if __name__ == '__main__':
    print('Starting BJJ Academy Bot API...')
    print('Navigate to http://localhost:5000')
    app.run(debug=True, host='127.0.0.1', port=5000)
