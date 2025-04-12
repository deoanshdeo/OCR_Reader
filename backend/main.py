# This is the starting point for running our web app!

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Starts the app in "developer mode" for testing on my computer.
    app.run(debug=True, host='0.0.0.0', port=5000)