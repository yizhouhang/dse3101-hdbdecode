<p align="center">
  <img src="./image/photo.jpeg" alt="Team Logo" width="200"/>
</p>

# Overview 
Buying or selling an HDB flat in Singapore comes with various challenges. 
Users interested in specific units often struggle to determine a fair market price, as listing platforms typically reflect inflated asking prices rather than actual transaction values—especially in non-seller’s markets. For general buyers, the process can be overwhelming due to the number of factors to consider, such as budget,location,flat type, nearby amenities,etc.
With information scattered across multiple sources, it’s difficult for users to make confident, informed decisions.


## Our Goal

We aim to develop an **intuitive and interactive digital platform** to help users confidently navigate the HDB resale market. The platform provides:
- Insights into current resale price trends
- Accurate price predictions for specific units
- Personalised home recommendations through a user-friendly filtering system

## Who This Is For

Our web application is designed for:
- **HDB homeowners** looking to sell or assess their current flat's value  
- **Buyers with specific flats in mind** who want to verify whether the asking price is fair  
- **General buyers** searching for suitable flats based on preferences like budget, location, or lifestyle

## Key Features

- 📊 **Resale price trends**: General market analysis and filtered trends based on user-selected criteria (e.g. location, flat type, lease left)  
- 🔍 **Price prediction**: Predict resale prices for specific HDB units  
- 🏡 **Home recommendations**: Suggest flats tailored to the user's preferences  
- 🗺️ **Map-based exploration**: Visualise flats by location and proximity to amenities

## Tools & Technologies

- **Frontend**: Streamlit  
- **Backend**: pandas, numpy, scikit-learn  

## Watch the videos to learn more

### User Guide  
[![Watch the User Guide](https://img.youtube.com/vi/wcmuvZuAzoc/0.jpg)](https://www.youtube.com/watch?v=wcmuvZuAzoc&t=27s)

### Technical Explanation  
[![Watch the Technical Explanation](https://img.youtube.com/vi/pBSm2NfJKlg/0.jpg)](https://www.youtube.com/watch?v=pBSm2NfJKlg)

# Dataset Download & Setup Guide
##  Dataset Download
Large datasets are available on [Google Drive](https://drive.google.com/drive/folders/1da-2bW0eXB41yyAi8cQMKaaZb4EyZ61h?usp=sharing).

##  Setup Instructions
After downloading, place the datasets into the `/data` folder located at the root of the project directory in order to run the scripts.

# How to Run Our App with Docker 

Follow these steps to set up and run our application using Docker:

## 1. Log in to Docker Hub
Visit [https://hub.docker.com/](https://hub.docker.com/) and sign in with your Docker account. If you don’t have one, you’ll need to create an account first.

## 2. Download and Install Docker Desktop
Go to [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/) and download Docker Desktop for your operating system.  
After downloading, follow the installation instructions to set it up.

## 3. Run the App
- Open Docker Desktop and make sure it’s running.  
- Open a terminal (Command Prompt, PowerShell, or Terminal depending on your OS).  
- Pull and run the Docker image using the following commands:

```bash
docker pull yuntsingg/hdbdecode
```
```bash
docker run -p 8501:8501 yuntsingg/hdbdecode
```

- Once the container starts, you can access the app in your browser at:  
[http://localhost:8501](http://localhost:8501)

---

If there are any issues or additional setup steps (like environment variables or volume mounts), please contact the team via email hdbdecode@gmail.com. 





