# Chess Assistant

## Project Overview

Chess Assistant is an interactive tool that allows users to set chess positions on a virtual board and request a strategic analysis of the position through a chatbot. Users can choose between receiving a general report on the position or focusing on specific aspects, such as the pawn structure, piece activity, and others. The project leverages advanced natural language processing technologies via LLMs to provide understandable and useful natural language analyses, going beyond traditional chess engines that only provide the best move.

## Project Components

The project consists of two main services that work together to provide the complete functionality:

- **api-server**  
  This is the backend service that receives chess positions and generates strategic reports requested by the user using ChatGPT for analysis. It is developed in Python and Flask.

- **web-client**  
  This is the frontend service, a web interface that allows users to set chess positions on a virtual board and request reports on the positions they configure. This component is developed with Node.js and React, providing an intuitive and user-friendly interface.

## Use of Stockfish

The backend uses a modified version of Stockfish 15.1, which includes text traces with relevant strategic information about the chess position. These traces provide additional details that are used by the language model (ChatGPT) to generate more comprehensive and accurate analyses. The modified version of Stockfish can be found in the repository [StockfishTraces](https://github.com/pCarmonaa/StockfishTraces).

To run the service manually, you need to download this project, compile it, and place the resulting `stockfish` executable in the `api-server/stockfish` directory. This allows the backend to access Stockfish for position analysis before passing the information to the language model.

## Running the Project

### Option 1: Running with Docker

1. **Configuring the ChatGPT Token:**  
   You need to configure the ChatGPT token in the environment variables for the `api-server` service, within the `docker-compose.yml` file. Other environment variables are optional, but the default configuration should work fine.

2. **Starting the Services with Docker:**  
   Once the environment variables are set, you can run the following command in the project’s root directory:
   ```bash
   docker compose up --build
   ```
   This command will build and start both the backend (`api-server`) and frontend (`web-client`) services, using the configurations defined in the `docker-compose.yml` file.

### Option 2: Running Manually

#### 1. Configuring the ChatGPT Token  
   You need to edit the `.env` file located in `api-server/.env` to set the ChatGPT token. Other configuration properties in the `.env` file can also be modified, but the default configuration is valid.

#### 2. Creating a Python Virtual Environment (Optional but Recommended)  
   It is recommended to create a virtual environment to isolate the project's dependencies. Run the following commands in the `api-server` directory:

   ```bash
   cd api-server
   python -m venv chess-assistant
   source chess-assistant/bin/activate  # On Windows: chess-assistant\Scripts\activate
   ```

#### 3. Installing Backend Dependencies  
   Once the virtual environment is activated, install the required dependencies for the backend by running:
   ```bash
   pip install -r requirements.txt
   ```

#### 4. Download and Compile Modified Stockfish  
   Download the modified version of Stockfish from the following repository:  
   [StockfishTraces](https://github.com/pCarmonaa/StockfishTraces).  
   Compile it and copy the `stockfish` executable to the `api-server/stockfish` folder.

#### 5. Running the Backend Manually  
   With the virtual environment activated, dependencies installed, and Stockfish configured, you can start the backend service by running:
   ```bash
   python src/app.py
   ```

#### 6. Running the Frontend Manually  
   Navigate to the `web-client` directory, install the Node.js dependencies, and start the frontend server with the following commands:

   ```bash
   cd web-client
   npm install
   npm start
   ```

With both services running, the application will be ready to interact and generate strategic chess analyses.