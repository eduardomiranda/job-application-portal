from pymongo import MongoClient
from bson.objectid import ObjectId
import tomli


def get_mongodb_collection(mongodb_uri, db_name, collection_name):
    """
    Connects to a MongoDB collection and returns the collection reference.

    Parameters:
    - mongodb_uri: URI string to connect to MongoDB.
    - db_name: The name of the database.
    - collection_name: The name of the collection.

    Returns:
    - Reference to the collection in the database.
    """
    try:
        # Create MongoDB client
        client = MongoClient(mongodb_uri)

        # Obtain reference to the database
        db = client[db_name]

        # Obtain reference to the collection
        collection = db[collection_name]

        return client, collection
    except Exception as e:
        print(f"An error occurred while connecting to MongoDB: {e}")
        return None




def salva_no_mongo( mongodb_uri, db_name, collection_name, json ):

	client, collection = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	resultado = collection.insert_one(json) # Insere o documento na coleção
	client.close()

	return resultado.inserted_id




def consulta_varios_documentos( mongodb_uri, db_name, collection_name, query ):

	client, collection  = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	cursor = collection.find(query) # Seleciona os documentos que correspondem à query de consulta
	docs = list( cursor )
	client.close()

	return docs



def consulta_um_unico_documento( mongodb_uri, db_name, collection_name, query ):

	client, collection = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	documento = collection.find_one(query) # Seleciona os documentos que correspondem à query de consulta
	client.close()

	return documento




def atualizar_um_unico_documento( mongodb_uri, db_name, collection_name, query_filtro, query_update ):

	client, collection = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	resultado = collection.update_one(query_filtro, query_update)
	client.close()

	return resultado




def atualizar_varios_documentos( mongodb_uri, db_name, collection_name, query_filtro, query_update ):

	client, collection = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	collection.update_many(query_filtro, query_update)
	client.close()




def excluir_varios_documentos( mongodb_uri, db_name, collection_name, query ):

	client, collection = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	collection.delete_many(query)
	client.close()



def excluir_documento_via_ObjectId( mongodb_uri, db_name, collection_name, objectid ):

	client, collection = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	query = {"_id": ObjectId( objectid )}
	collection.delete_one(query)
	client.close()



def aggregate(mongodb_uri, db_name, collection_name, pipeline):

	client, collection = get_mongodb_collection(mongodb_uri, db_name, collection_name)
	cursor = collection.aggregate(pipeline)
	docs = list( cursor )

	client.close()

	return docs



# Example usage
if __name__ == "__main__":

	# Leitura do arquivo de configurações
	with open("config.toml", mode="rb") as f:
		config = tomli.load(f)

	mongodb_uri = config['mongodb']['mongodb_uri']
	db          = config['mongodb']['db']
	collection  = config['mongodb']['collection']
	query = {'assessment_id': 'a17a71e6-17c8-414a-b613-84c1df55dfcb'}

	docs = consulta_um_unico_documento(mongodb_uri, db, collection, query)

	print(docs)

