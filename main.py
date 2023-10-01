import os

from app import app
import callbacks

server=app.server

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8051)))
    
