# How to run

## Preliminary setup

### Back-end

To run Economics AI:
- The Raku package ["LLM::Containerization"](https://raku.land/zef:antononcube/LLM::Containerization) has to be installed.
  A LLaMA (llamafile) model has to be accessible
  - For example, "Llama-3.2-1B-Instruct.Q6_K.llamafile"
    - Which can be run with the command `llamafiler --model Llama-3.2-1B-Instruct.Q6_K.llamafile`.
- A search index over the texts has to be created with vector embeddings of that model
  - Using ["LLM::RetrievalAugmentedGeneration"](https://raku.land/zef:antononcube/LLM::RetrievalAugmentedGeneration).
- The search index has to be placed in "~/.local/share/raku/LLM/SemanticSearchIndex" 

#### macOS specific

- Download the GitHub repository ["raku-digest-sha1-native"](https://github.com/bduggan/raku-digest-sha1-native) and install it "locally."
  - This is needed for the installation of the package ["Cro::WebSocket"](https://raku.land/zef:cro/Cro::WebSocket).

### Front-end

- Install R and RStudio.
- Get the package ["DSLInterpretationInterfaces"](https://github.com/antononcube/R-packages/tree/master/DSLInterpretationInterfaces).
  - From the repository [antononcube/R-packages](https://github.com/antononcube/R-packages).
- Install the R-package ["ExternalParsersHookUp"](https://github.com/antononcube/ConversationalAgents/tree/master/Packages/R/ExternalParsersHookUp):
  - `devtools::install_github(repo = "antononcube/ConversationalAgents", subdir = "Packages/R/ExternalParsersHookUp")`
- Make sure the front-end interface "RAG-evaluations.Rmd" works with the back-end.
  - Placed in the directory ["RAGs-flexdashboard"](https://github.com/antononcube/R-packages/tree/master/DSLInterpretationInterfaces/RAGs-flexdashboard).
- Publish to "RAG-evaluations" [shinyapps.io](https://www.shinyapps.io).

### Run back-end on a remote server

- Assuming using a server on a cloud computing platform
  - Like [DigitalOcean](https://www.digitalocean.com) or similar
- Make two screens: "llamafile" and "ragui"
  - Using the UNIX/Linux command [`screen`](https://www.gnu.org/software/screen/manual/screen.html) 
- In the screen "llamafile" start the LLaMA file model
  - For example, `llamafiler --model Llama-3.2-1B-Instruct.Q6_K.llamafile`.
- In the screen "ragui" start the LLM web service with:
  - `llm-web-service --host=accendodata.net --port=5080`
- In the front-end, shinyapps.io interface ["RAG-evaluations"](https://antononcube.shinyapps.io/RAG-evaluations/)
  - Go to the "Setup" panel:
    - Place the correct Web service URL ("http://accendodata.net:5080")
    - Configure LLaMA embeddings model (default should be fine)
    - Configure "post-processing" LLM model

------

## Verify existing run setup

- Assuming the EconomicsAI service is installed on cloud computing server
  - To be concrete, on a Ubuntu [DigitalOcean](https://www.digitalocean.com) droplet 
- See the available screens
  - Using the command `screen -ls`
  - Log to existing screen with `screen -r <name>`
- Is there a screen named "llamafile"?
  - If no make one and run the command:

```
llamafiler --model Llama-3.2-1B-Instruct.Q6_K.llamafile
```

- If there a screen named "ragui"?
  - If not make one and run the command:
  
```
llm-web-service --host=accendodata.net --port=5080
```

That might be slow -- wait until you see the message:

> Started the Cro service.

-----

## Troubleshooting

### Cannot start a new llamafile model

If the command :

```
llamafiler --model Llama-3.2-1B-Instruct.Q6_K.llamafile
```

Gives the error:

> 127.0.0.1:8080: Address already in use

Then see the output of:

```
sudo lsof -i :8080
```

Kill the PID process with `kill -9 <PID>`.