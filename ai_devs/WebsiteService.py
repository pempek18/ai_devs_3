import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS

class WebsiteService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
    def _fetch_website_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text()
        except Exception as e:
            raise Exception(f"Error fetching website content: {str(e)}")

    def _create_vector_store(self, text):
        chunks = self.text_splitter.split_text(text)
        return FAISS.from_texts(chunks, self.embeddings)

    def run(self, link, question):
        # Fetch and process website content
        content = self._fetch_website_content(link)
        # Get all links from the main page
        soup = BeautifulSoup(requests.get(link).text, 'html.parser')
        base_url = '/'.join(link.split('/')[:3])  # Get base domain
        
        # Find all links and filter for internal ones
        all_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):
                # Convert relative to absolute URL
                full_url = base_url + href
                all_links.append(full_url)
            elif href.startswith(base_url):
                all_links.append(href)
                
        # Fetch content from all subpages
        all_content = content
        for subpage_url in all_links:
            try:
                subpage_content = self._fetch_website_content(subpage_url)
                # Parse subpage for additional links
                subsoup = BeautifulSoup(requests.get(subpage_url).text, 'html.parser')
                subpage_links = []
                for sub_a_tag in subsoup.find_all('a', href=True):
                    href = sub_a_tag['href']
                    if href.startswith('/'):
                        full_url = base_url + href
                        if full_url not in all_links and full_url not in subpage_links:
                            subpage_links.append(full_url)
                    elif href.startswith(base_url):
                        if href not in all_links and href not in subpage_links:
                            subpage_links.append(href)
                
                # Fetch content from subsubpages
                for subsubpage_url in subpage_links:
                    try:
                        subsubpage_content = self._fetch_website_content(subsubpage_url)
                        all_content += "\n\n" + subsubpage_content
                    except Exception as e:
                        print(f"Error fetching {subsubpage_url}: {str(e)}")
                        continue
                all_content += "\n\n" + subpage_content
            except Exception as e:
                print(f"Error fetching {subpage_url}: {str(e)}")
                continue
                
        # Use combined content from main page and subpages
        content = all_content
        # Create vector store from the content
        vector_store = self._create_vector_store(content)
        
        # Set up conversation chain
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vector_store.as_retriever(),
            memory=memory
        )
        
        # Get answer
        result = qa_chain({"question": question})
        return result["answer"]

if __name__ == "__main__":
    service = WebsiteService()
    print(service.run("https://softo.ag3nts.org/", "Jak nazywa się firma zbrojeniowa produkująca roboty przemysłowe i militarne?"))
    print(service.run("https://softo.ag3nts.org/", "Jakie są produkty firmy Softo?"))