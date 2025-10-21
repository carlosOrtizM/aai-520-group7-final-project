<div align="center">
<img align="center" width="30%" alt="image" src="https://www.sandiego.edu/assets/global/images/logos/logo-usd.png">
</div>

# Multi-Agent Financial Advisor

![](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![](https://img.shields.io/badge/MSAAI-NLP-blue?style=for-the-badge)
![](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)

aai-520-group7-final-project

## Table of Contents
- [Description](#Overview)
- [License](#license)

#### Github Project Structure

```
├── README.md                             # Project documentation (this file)
└── .gitignore                            # Ignored files for Git
└── g(old)                                # Archived files
└── final-project-ipynbs                  # Final agent/workflow code files
└── persistence                           # File I/O Storage

```

# Overview
## About the Project

This is a multi-agent/workflow demo (.ipynbs) built on top of Langgraph and Langchain. The workflows/agents include:
- An earnings_calendar_provider
- A market_news_provider
- A news_aggregator_chain
- A price_history_provider
- A rag_bot
- A stock_news_deep_provider
- A yf_news_provider

## Run it yourself?

Clone the GitHub repo and be sure to download necessary libraries or external SW (where needed)

We are using Ollama for Llm hosting and ChromaDB for the vector/embedding DB, as they are both beginner-friendly and
allow for <b>local</b> deployment.

So... you need to download Ollama. To get the Ollama latest versions, go to their website:

Ollama:
https://ollama.com/download

Also, if you don't have Python downloaded, it is necessary as well... so go ahead and grab it.

Python:
https://www.python.org/downloads/

Also i you want to run the .pdf Preprocessing locally (Unstructured) you'll need to download Poppler, Tesseract, and Magic as well. Use brew for MacOS and for Linux use your package manager (or download the binaries accordingly).

## Contributors
<table>
  <tr>
    <td>
        <a href="https://github.com/carlosOrtizM">
          <img src="https://github.com/carlosOrtizM.png" width="100" height="100" alt="Carlos Ortiz "/><br />
          <sub><b>Carlos Ortiz</b></sub>
        </a>
      </td>
      <td>
        <a href="https://github.com/aditithakur-569">
          <img src="https://github.com/aditithakur-569.png" width="100" height="100" alt="Adhiti Jha "/><br />
          <sub><b>Adhiti Jha</b></sub>
        </a>
      </td>
  </tr>
</table>

## License

MIT License

Copyright (c) [2025]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
