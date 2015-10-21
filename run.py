#!/usr/bin/env python
from app import app

# invoke run method to start server
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000,debug = True)
