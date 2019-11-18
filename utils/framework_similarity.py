from os import listdir
from json import loads
from pathlib import Path
from yaml import full_load
from gensim.similarities import Similarity
from gensim.corpora.textcorpus import TextDirectoryCorpus
from gensim.corpora import MmCorpus
from gensim.test.utils import (
    get_tmpfile
)


class FrameworkSimilarity(object):
    def __init__(self,
                 framework_type="competency",
                 framework_dir="./frameworks",
                 top_n=30,
                 norm='l2'):
        self.framework_type = framework_type
        self.framework_dir = framework_dir
        self.framework_name_to_id = {}
        self.row_to_framework_name = []
        self.row_to_framework_id = []      
        self.shard_prefix = get_tmpfile(f"{framework_type}_index")
        self._corpus = TextDirectoryCorpus(f"{framework_dir}/{framework_type}",
                                           lines_are_documents=False,
                                           metadata=True)

        MmCorpus.serialize(f"{framework_type}.mm",
                           self._corpus,
                           id2word=self._corpus.dictionary.id2token,
                           metadata=True)
        self.corpus = MmCorpus(f"{framework_type}.mm")

        self.similarities = Similarity(self.shard_prefix,
                                       self.corpus,
                                       num_features=self.corpus.num_terms,
                                       num_best=top_n)
        self.construct_framework_arrays()
        # for framework in loads(Path("./frameworks/framework_metadata.json").read_text()):
        #     self.framework_name_to_id[framework['filename']] = framework['framework_id']


    def construct_framework_arrays(self):
        for row, framework in enumerate(
            listdir(
                self.framework_dir+self.framework_type)):
            
            with open(self.framework_dir+self.framework_type+'/'+framework, 'r') as stream:
                config = full_load(stream)
                self.row_to_framework_id.append( config['framework_id'] )
                self.row_to_framework_name.append( config['framework_name'] )

        # for row, framework in enumerate(listdir(self.framework_dir+self.framework_type)):
        #     framework_name = framework #.split('.')[0]
        #     self.row_to_framework_name[row] = framework_name
        #     self.framework_to_row[framework_name] = row

    def framework_recommedation(self, raw_job_description):
        #  todo: add more logic around parsing the context object and
        # returning specific recommendations
        
        vec_bow = self._corpus.dictionary\
                              .doc2bow(
                                  raw_job_description.lower()
                                                     .split())
        sims = self.similarities[vec_bow]
        return [(
                self.row_to_framework_name[sim[0]],
                sim[1],
                self.row_to_framework_id[sim[0]]
            ) for sim in sims]

        # return [
        #     (
        #         self.row_to_framework_name[sim[0]],
        #         sim[1],
        #         self.framework_name_to_id[
        #             self.row_to_framework_name[sim[0]]
        #         ]
        #     )

        #             for sim in sims]
