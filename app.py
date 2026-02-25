from dashboard.app import app
import os

if __name__ == "__main__":
    # Ensure we are in the root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Use the port assigned by the hosting platform or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
