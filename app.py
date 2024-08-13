import streamlit as st
import pandas as pd
import requests 
from bs4 import BeautifulSoup
import pdfplumber
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Laad de omgevingsvariabelen uit het .env bestand dit is getest
load_dotenv()

# Haal de API-key op uit de omgevingsvariabelen
api_key = os.getenv("OPENAI_API_KEY")


# Controleer of de API-key is ingesteld
if api_key is None:
    st.error("OPENAI_API_KEY is niet ingesteld. Voeg deze toe aan je .env bestand.")
    st.stop()

# Initialiseer ChatOpenAI met de API-key en het nieuwe model
llm = ChatOpenAI(model_name="gpt-3.5-turbo", max_tokens=500, api_key=api_key)

# Functie om de vacaturetekst te halen van de link
def get_job_description(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise een exception als de status code niet 200 is
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.exceptions.RequestException as e:
        st.error(f"Fout bij het ophalen van de vacaturetekst: {e}")
        st.stop()

# Functie om de motivatiebrief te genereren
def generate_cover_letter(cv_text, job_description):
    # Maak een prompt template
    prompt_template = PromptTemplate(
        input_variables=["cv_text", "job_description"],
        template="""CV: {cv_text}\nVacature: {job_description}\nMotivatiebrief: 
        Maak hier de allerbeste motivatievbrief die je kan bedenken. Start de eerste zin altijd met een pakkende zin die gerelateerd 
        is aan het onderwerp van de functie, vertel niet over jezelf maar juist over het onderwerp, voorwaarde hiervoor is dat het aansluit bij de functie en het onderwerp. Zodat het laat zien dat je actuele kennis hebt. 
        Maak gebruik van de persoonlijke informatie uit de cv en vacature tekst Zie voor de aanhef de naam die bij de vacatures staat. Vermijd standaardzinnen zoals: Met veel enthousiasme.. "
    """)
    
    # Initialiseer LLMChain
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    # Genereer de motivatiebrief
    cover_letter = chain.run({"cv_text": cv_text, "job_description": job_description})
    
    return cover_letter

# Streamlit interface
st.title("HireMe - Motivatiebrief Generator")

st.header("Upload je CV")
cv_file = st.file_uploader("Kies een PDF of tekstbestand", type=['pdf', 'txt'])

st.header("Geef de link van de vacature")
job_url = st.text_input("Vacature URL")

if st.button("Genereer Motivatiebrief"):
    if cv_file is not None and job_url:
        # Laadindicator
        with st.spinner("Bezig met genereren..."):
            # Lees de CV tekst
            if cv_file.type == "application/pdf":
                cv_text = ""
                try:
                    with pdfplumber.open(cv_file) as pdf:
                        for page in pdf.pages:
                            cv_text += page.extract_text() or ""
                except Exception as e:
                    st.error(f"Fout bij het lezen van het PDF-bestand: {e}")
                    st.stop()
            else:
                try:
                    cv_text = cv_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    st.error("Fout bij het lezen van het tekstbestand. Controleer of het bestand in UTF-8 formaat is.")
                    st.stop()
            
            # Haal de vacaturetekst op
            try:
                job_description = get_job_description(job_url)
            except Exception as e:
                st.error(f"Fout bij het ophalen van de vacaturetekst: {e}")
                st.stop()
            
            # Genereer de motivatiebrief
            cover_letter = generate_cover_letter(cv_text, job_description)
            
            st.subheader("Je motivatiebrief:")
            st.write(cover_letter)