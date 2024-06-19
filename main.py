import requests as re
from bs4 import BeautifulSoup
import pandas as pd
import os
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

urls = {
    "CNN": "https://edition.cnn.com/",
    "BBC": "https://www.bbc.com/"
}

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

def get_articles(url, headers):
    print("Accessing websites ...")
    response = re.get(url, headers=headers)
    response.encoding = response.apparent_encoding
    articles = []

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html5lib')

        if 'bbc' in url:
            div_titreBBC = soup.find('div', class_="sc-5b94fa74-0 sc-e70150c3-3 jbFGkZ kdbokE")
            if div_titreBBC:
                e_titresBBC = div_titreBBC.find_all("h2", class_="sc-4fedabc7-3 zTZri")
                e_linksBBC = div_titreBBC.find_all("a", class_="sc-2e6baa30-0 gILusN")
                for e_titreBBC, e_linkBBC in zip(e_titresBBC, e_linksBBC):
                    title = e_titreBBC.text.strip()
                    link = "https://www.bbc.com" + e_linkBBC['href']
                    content = get_article_content(link, 'bbc', headers)
                    articles.append((title, link, content))
        elif 'cnn' in url:
            div_titreCNN = soup.find('div', class_="stack__items")
            if div_titreCNN:
                e_titresCNN = div_titreCNN.find_all("span", class_="container__headline-text")
                for e_titreCNN in e_titresCNN:
                    title = e_titreCNN.text.strip()
                    link = "https://edition.cnn.com" + e_titreCNN.find_parent('a')['href']
                    content = get_article_content(link, 'cnn', headers)
                    articles.append((title, link, content))
    else:
        print('ERREUR : ', response.status_code)
    return articles

def get_article_content(article_url, source, headers):
    try:
        response = re.get(article_url, headers=headers)
        response.encoding = response.apparent_encoding
        content = ""

        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html5lib')

            if source == 'bbc':
                div_content = soup.find('div', class_="app")
                if div_content:
                    paragraphs = div_content.find_all('p', class_="sc-eb7bd5f6-0 fYAfXe")
                    content = " ".join(p.text.strip() for p in paragraphs)
            elif source == 'cnn':
                div_content = soup.find('div', class_="article__content")
                if div_content:
                    paragraphs = div_content.find_all('p', class_="paragraph inline-placeholder vossi-paragraph-primary-core-light")
                    content = " ".join(p.text.strip() for p in paragraphs)
        else:
            print(f'ERREUR : {response.status_code} lors de la récupération du contenu de l\'article {article_url}')
            content = f"Error {response.status_code}: Unable to retrieve article content."

    except re.RequestException as e:
        print(f'Erreur lors de la tentative d\'accès à l\'article {article_url} : {e}')
        content = ""

    return content

def summarize_all_articles(contents):
    print("Summarizing all articles...")
    combined_content = "\n\n".join(contents)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a journalist and want to summarize articles."},
            {"role": "user", "content": f"Summarize the following articles into a single but detailled summary of the current news:\n\n{combined_content}"}
        ],
        max_tokens=2000
    )
    summary = response.choices[0].message['content'].strip()
    tokens_used = response['usage']['total_tokens']

    with open("summary.txt", "w") as file:
        file.write(summary)

    print("Requête ChatGPT terminée ! Token utilisés : ", tokens_used)
    return summary, tokens_used

all_articles = []
all_contents = []
token_usage = []

for source, url in urls.items():
    articles = get_articles(url, HEADERS)
    for title, link, content in articles:
        all_articles.append((source, title, link, content))
        all_contents.append(content)

df = pd.DataFrame(all_articles, columns=['Source', 'Title', 'URL', 'Content'])

summary, tokens_used = summarize_all_articles(all_contents)
print("\nRésumé global de l'actualité :\n", summary)

df_summary = pd.DataFrame([['ALL', 'Résumé global', '', summary]], columns=['Source', 'Title', 'URL', 'Content'])
df = pd.concat([df, df_summary], ignore_index=True)
df['Tokens Used'] = [tokens_used if idx == len(df) - 1 else '' for idx in range(len(df))]
df.to_csv("news_summary.csv", index=False)
pd.set_option('display.max_colwidth', None)

#print("\n",df)



