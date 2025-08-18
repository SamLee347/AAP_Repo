import os
import google.generativeai as genai
from dotenv import load_dotenv
from Database.db import SessionLocal, init_db
from Database_Table import Inventory, Order
import numpy as np

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def getDbContent():
    session = SessionLocal()
    # You can join Inventory & Order if needed, or fetch separately
    inventory_records = session.query(Inventory).all()
    order_records = session.query(Order).all()
    session.close()
    return inventory_records, order_records

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def embed_content(records):
    embeddings_list = []
    for r in records:
        if isinstance(r, Inventory):
            text = (
                f"ItemId: {r.ItemId}, Date: {r.Date}, Quantity: {r.ItemQuantity}, "
                f"Category: {r.ItemCategory}, UnitsSold: {r.UnitsSold}, "
                f"Weight: {r.Weight}, Size: {r.Size}, Priority: {r.Priority}, "
                f"Dispose: {r.Dispose}"
            )
            record_id = r.ItemId
        elif isinstance(r, Order):
            text = (
                f"OrderId: {r.OrderId}, ItemId: {r.ItemId}, OrderQuantity: {r.OrderQuantity}, "
                f"Sales: {r.Sales}, Price: {r.Price}, Discount: {r.Discount}, "
                f"Profit: {r.Profit}, DateOrdered: {r.DateOrdered}, "
                f"DateReceived: {r.DateReceived}, CustomerSegment: {r.CustomerSegment}"
            )
            record_id = r.OrderId
        else:
            continue
        
        embedding = genai.embed_content(
            model="models/text-embedding-004",
            content=text
        )["embedding"]
        embeddings_list.append({"id": record_id, "text": text, "embedding": embedding})
    
    return embeddings_list

def query_gemini(question, top_k=3):
    # Embed question
    query_emb = np.array(genai.embed_content(
        model="models/text-embedding-004", content=question
    )["embedding"])

    #Embed database content
    inventory, order = getDbContent()
    embeddings_list = embed_content(inventory + order)

    # Compute similarity
    sims = []
    for item in embeddings_list:
        emb = np.array(item["embedding"])
        sims.append((cosine_similarity(query_emb, emb), item["text"]))

    # Pick top_k records
    sims.sort(reverse=True, key=lambda x: x[0])
    top_texts = [text for _, text in sims[:top_k]]

    # Build prompt
    context = "\n\n".join(top_texts)
    prompt = f"""
    You are an assistant that answers strictly from the provided context.
    If the context does not contain the answer, say "I could not find that in the database."

    Context:
    {context}

    Question:
    {question}
    """

    # Ask Gemini
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text



