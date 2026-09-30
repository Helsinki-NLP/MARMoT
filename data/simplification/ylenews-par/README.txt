Parallel Corpus of Finnish and Easy-to-read Finnish from the Yle News Archive 2014-2018, source

Suomi-selkosuomi-rinnakkaiskorpus Ylen suomenkielisestä uutisarkistosta 2014-2018, lähdeaineisto

Shortname: ylenews-fi-2014-2018-selko-par-src

Metadata: http://urn.fi/urn:nbn:fi:lb-2024011701

Rightholder: Yleisradio

License: CLARIN ACA +NC +OTHER v2.1
The complete license is available at http://urn.fi/urn:nbn:fi:lb-2022050901

A copy of the license is included in LICENSE.txt. The license details
may be subject to change, so before downloading the resource, please
refer to the latest version of the license at the above link.


CORPUS DESCRIPTION
This is a parallel corpus created of the Yle news articles from 2014-2018
by aligning the standard Finnish versions with the easy-language versions.
The dataset, created by Anna Dmitrieva and available in CSV format, is aligned
on the document level.
The news articles were obtained from the datasets available via Kielipankki
(http://urn.fi/urn:nbn:fi:lb-2017070501 and http://urn.fi/urn:nbn:fi:lb-2019050901).

This dataset extends the previously published Parallel Corpus of Finnish
and Easy-to-read Finnish from the Yle News Archive 2019-2020
(http://urn.fi/urn:nbn:fi:lb-2022111625).
Please note that this dataset has not been assessed by a human expert.
The articles have been aligned automatically with the Vecalign document
alignment algorithm (https://github.com/thompsonb/vecalign) without candidate
rescoring, using LASER embeddings (https://github.com/facebookresearch/LASER).

Description of all columns in the dataset:
- index_in_selko: This index consists of two parts divided by an underscore.
  The first (longer) part identifies the entire Easy Finnish article from the
  original dataset. The second (shorter) part is the number of the paragraph.
  Since the Yle Selkosuomi articles usually consist of multiple paragraphs,
  each paragraph describing a separate piece of news, we represent each
  paragraph as an individual little article in our dataset.
  Paragraph numbering starts with 0.
- index_in_regular: The identifier of the regular Finnish article taken from
  the original dataset.
- selko_text: A piece of news in Easy Finnish.
- regular_text: A corresponding piece of news in regular Finnish.
- distance: The cosine distance between the document vectors. The lower the
  distance, the more similar the documents are.


For further information, please contact fin-clarin@helsinki.fi .
