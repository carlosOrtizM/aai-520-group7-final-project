from langchain_ollama import ChatOllama
from configparser import ConfigParser

# these config parsers are something I want to get rid of and instead use the .env file
# what they were doing was basically fetch some important "Global settings" type of information that we wanted not
# to be hard-coded. For example, if I changed the llm I was going to be using I would just go to the global settings and
# change that parameter and not have to go change the model name everywhere it was going to be used.

# something else I wanted to change in all .pys was the overall function definition, there are no try catch blocks,
# in case something breaks (and we would get the console red ugly text bibles printed out)

def model_fetcher():
    # Create a ConfigParser object
    config_object = ConfigParser()

    # Read the configuration from the 'config.ini' file
    config_object.read("config.ini")

    # Access the Path section
    model = config_object["Llm"]

    return model["name"]

# here we are instantiating an Ollama chat client into our program. It is worth going back to our conversation on
# langchain as middleware (agent_creator.py) to further discuss how other external services/libraries are being
# employed. As we've stated we plan to use Ollama as our "Llm model provider" and ChromaDB as our vector Embedding DB*.

# So, we are self-hosting some services but, what does that mean? In our case it means we need to go and download these
# applications and have them running in our computer (have the Ollama and ChromaDB servers up and running. It might
# sound like something extremely technical but the truth is it is not, and it happens with most applications we use in
# our day-to-lives. Note: what I'm about to state next comes from personal experience alone. I didn't major in
# Computer Science, so the theory might be a bit off.

# The reason we need to set up these applications as servers is because these "self-contained" software systems need to
# communicate with other software systems (inside our computer or out in the internet), and they do so by taking up
# a designated port in the computer. Kind of like how APIs take a specific URI (ollama.com/fetch/cookie), and calling on
# them is going to call on some specific method on a software system, on a lower level if we call on a specific port
# (8080) we expect our web browser to be ready to receive or send information. So, we need to set up Ollama and ChromaDB
# servers because they (of course) communicate with other systems (our application for instance). This servers exist
# for most big applications, yet we don't have to set them up because the developers set up a couple of scripts to set
# them up. (What I was primitively trying to do).

# This setting up the servers is independent of our program. We are setting up services because we want them up and
# running. And yes we want them to be in contact with our finance application, but setting them up is NOT like a method
# that we are triggering in our python code. Setting up the servers is an independent task completely unrelated to our
# application.

# It is important to make this distinction (recognize them as independent self-contained entities), because that way it
# is easier to understand what is happening in the method below. Where we are setting up a client (an object in our
# application) that is trying to establish a connection with that other system (in this case Ollama).

def llm_generator():
    # Initialize the LLM with model
    llm = ChatOllama(
        model=model_fetcher(),
        temperature=0.2,
    )

    return llm

# So we need to go Download ollama, and set up the server as per the documentation, and for ChromaDB what is different
# is the fact that we are not downloading an application but rather a library, and running that library as a server.

# This is a very interesting turn of events that opens up the floor to write about two things that come up quite often
# in Python: libraries and python virtual environments.

# Libraries could be seen as a black boxes of functions that serve a given purpose, and by downloading these bags of
# functions we are able to use them without having to understand how is it they are getting things done.
# If libraries start to get bigger and bigger, and require connections with other applications, and can be allocated
# storage space, and can speak with the OS of the computer, and have a User Interface, then we have applications.

# In our case ChromaDB (and most other vector embedding dbs) are cloud-centric (the Chroma guys host
# and make money of it; monopolize access to their product by selling API tokens/usage). So giving the final user a
# desktop product is not something on the roadmap. They thankfully do have a self-hosted option, but the fact it comes
# as a library shows that it might have started as an Open Source library, but they figured they could make money of it
# and went for a cloud-based product. Or that they were always a cloud-native product, but decided to give a taste to
# users to run "just enough" locally and eventually turn to a more premium set of features on the cloud... or something
# else entirely.

# *It might me more dificult to set up initially, but for more robust Systems I would go for elasticsearch instead of
# ChromaDB (vector search is not enough...).
# https://www.elastic.co/search-labs/blog/rag-graph-traversal
# https://www.elastic.co/search-labs/blog/llm-agents-intelligent-hybrid-search ).

# The other thing we come across in python often: Virtual environments. To program in Python, we need three things. The
# python core libraries (black boxes of functions), a compiler, and an interpreter. The compiler is something that could
# be seen as a very specific core python library that is in charge of turning the human-readable functions made or used
# by the program into something more machine digestible (and executing those machine digestible transactions. If you add
# a new library or two the compiler is going to process them in the same way (as the language and structure is the same)
# . What goes on to change is the python interpreter.

# The interpreter could be seen as another core Python library in charge of taking in the human-readable code, making
# sense of it, and passing it to the compiler. What changes is that an interpreter might receive the function
# delete_everything() and know exactly what it means, while another interpreter will receive the same function and have
# absolutely no idea what it's supposed to do. The interpreter is context dependent, in the sense that it will know what
# to do based on the libraries it has downloaded it its environment.

# This is where those virtual environments come in... they are virtual because they all share a common ancestor:
# The python package downloaded in the computer. If one where to add non-standard libraries to this origianl python
# interpreter, they would be available to all child virtual environments as well. So, we set up this convenient forked
# environments to download particular libraries for our specific projects. And our particular interpreter is able to
# make sense of functions that would otherwise be alien to it.

# So we have libraries, interpreters, compilers... if we where to make them much more complicated we could end up with..
# an Operating System...

# this is only worth mentioning in this context to understand why we sometimes have to use the terminal for
# python commands and sometimes for Linux/Mac/Windows. What is going on is we are accessing two different worlds,
# most times from the same terminal. We could think of them as a city and a gated community inside the city.
# They have different ways of doing things, and they are modifying different environments...