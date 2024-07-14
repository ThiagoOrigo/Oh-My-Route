#!/bin/sh
python add_ga.py && streamlit run main.py --server.port $PORT --server.address 0.0.0.0
