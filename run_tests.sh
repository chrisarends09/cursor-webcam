#!/bin/bash

# Run pytest with coverage report
pytest --cov=app tests/ --cov-report=term-missing 