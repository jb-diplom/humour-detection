# humour-detection

## MSc Thesis Project UvA 2021<br>
Author: Janice Butler<br>University of Amsterdam, 2021<br><br>
A project to fine-tune neural language models (NLMs) for tasks involving the detection and measurement of humour-type and the degree of humour in a text. Much emphasis is placed on determining which NLM is optimal for this task and which hyperparameters are most efficient, but also most accurate in inference of the tasks.<br>

## Getting Started

The project is organised in 3 phases

1. Data capture: Data is scraped from both Reddit.com and Twitter.com. <br>The code for scraping is to be found in https://github.com/jb-diplom/humour-detection/tree/main/scraping
2. The scraped data is processed and annotated for use in fine-tuning of the NLMs. Intermediate raw data is saved in https://github.com/jb-diplom/humour-detection/tree/main/data-training and the final processed, randomly shuffled and segmented data is saved in https://github.com/jb-diplom/humour-detection/tree/main/data-training/complete. 3 Tasks are being trained for:
   * 5 degrees of humour plus the non-humorous category (k=6)
   * 2 degrees of humour (binary humour-recognition)  (k=2)
   * 9 types of humour: fun, benevolent humour, nonsense, wit, irony, satire, sarcasm, and cynicism k=9)
3. Once the data is annotated, shuffled and segmented it can be used to fine-tune the NLMs using the [Colab-Notebook] (https://github.com/jb-diplom/humour-detection/blob/main/notebooks/NLM_Trainer.ipynb)

### Prerequisites

To run the notebook there are no prerequesites except access to [Google Colab](https://colab.research.google.com/notebooks/intro.ipynb?utm_source=scs-index), since all the required libraries are installed in the first code-cell of the notebook:

The principal components used are 
* transformers              # huggingface framework for loading and training models, preprocessing of data
* wandb                     # for visualization of results on the project dashboard https://wandb.ai/jb-diplom/janice-final
* sentencepiece             # required for fine-tuning the deberta NLM
* chart_studio              # for visulization using Plotly Express
* google.colab.data_table   * A widget very useful for browsing dataframes and compatible with colab

## Usage

### Scraping reddit data

### Scraping Twitter Data

### Fine-Tuning 

#### Testing

### 

## Versioning

All code is versioned in Github in [this repository](https://github.com/jb-diplom/humour-detection). 

## Authors

* **Janice Butler** - *Initial work* - [Humour-Detection](https://github.com/jb-diplom/humour-detection)

## License

This project is licensed under the MIT License - see the [LICENSE.md](./LICENSE.md) file for details

## Acknowledgments

* Many thanks to my thesis supervisor [Dr. Damian Trilling](http://www.damiantrilling.net/) for basically letting me get on with it but providing advice and guidance as needed
