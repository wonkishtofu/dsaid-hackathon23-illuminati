"""Custom node post-processor for EMA solar chatbot."""

from llama_index.indices.postprocessor.node import BasePydanticNodePostprocessor
from llama_index.indices.query.schema import QueryBundle
from llama_index.indices.service_context import ServiceContext
from llama_index.data_structs.node import NodeWithScore
from llama_index.prompts.prompts import SimpleInputPrompt
from pydantic import Field
from typing import Optional, List, Set, cast
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


#Template to assess if query is about stats/data
DEFAULT_INFER_STATS_TMPL = (
    "A question is provided.\n"
    "The goal is to determine whether the question requires the provision of current figures, numbers"
    "or data.\n"
    "Questions related to future targets or past trends don't count.\n"
    "Please respond with YES or NO.\n"
    "Question: What is Singapore's installed solar capacity?\n"
    "Answer: YES\n"
    "Question: What is Singapore's solar target by 2030?\n"
    "Answer: NO\n"
    "Question: What is the total number of solar installations?\n"
    "Answer: YES\n"
    "Question: What is the solar panel deployment target by 2030?\n"
    "Answer: NO\n"
    "Question: How many solar PVs have been installed by non-residential private sector?\n"
    "Answer: YES\n"
    "Question: What schemes am I eligible for if I want to install solar PVs as a business owner?\n"
    "Answer: NO\n"
    "Question: {query_str}\n"
    "Answer: "
)

#Function to parse query type prediction
def parse_stats_pred(pred: str) -> bool:
    """Parse stats prediction."""
    if "YES" in pred:
        return True
    elif "NO" in pred:
        return False
    else:
        raise ValueError(f"Invalid stats prediction: {pred}.")


class CustomSolarPostprocessor(BasePydanticNodePostprocessor):
    """Custom node post-processor for EMA's solar chatbot.

    This post-processor does the following steps:

    - Decides query type
      (is it statistics/data-related?)
    - Sorts nodes by date.
    - If it is stats-related, to take the first k nodes (by default 1), and use that to synthesize an answer.
    - If it's not, to check if earliest 'Minister' node is > 2 years more outdated than a non-Minister node:
      - If yes, take earliest non-Minister node
      - If no, take earliest Minister node

    """

    service_context: ServiceContext
    top_k_recency: int = 1
    top_k_min: int = 2
    infer_stats_tmpl: str = Field(default=DEFAULT_INFER_STATS_TMPL)
    date_key: str = "date"
    category_key: str = "category"
    # if false, then search node info
    in_extra_info: bool = True

    def postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """Postprocess nodes."""

        if query_bundle is None:
            raise ValueError("Missing query bundle in extra info.")

        #query_bundle = cast(QueryBundle, extra_info["query_bundle"])
        infer_stats_prompt = SimpleInputPrompt(self.infer_stats_tmpl)
        raw_pred, _ = self.service_context.llm_predictor.predict(
            prompt=infer_stats_prompt,
            query_str=query_bundle.query_str,
        )
        pred = parse_stats_pred(raw_pred)
        print(f"Prediction on stats status: {pred}")

        # sort nodes by date
        info_dict_attr = "extra_info" if self.in_extra_info else "node_info"
        node_dates = pd.to_datetime(
            [getattr(node.node, info_dict_attr)[self.date_key] for node in nodes]
        )
        sorted_node_idxs = np.flip(node_dates.argsort())
        sorted_nodes = [nodes[idx] for idx in sorted_node_idxs]
        
        # Return most recent nodes if pred is True
        if pred:
            return sorted_nodes[: self.top_k_recency]
        else:
            # obtain Minister vs non-Minister nodes
            Min_only = [node for node in sorted_nodes if node.node.extra_info[self.category_key] == "Minister"]
            non_Min = [node for node in sorted_nodes if node.node.extra_info[self.category_key] != "Minister"]

            # compare dates of most recent Minister vs non-Minister nodes (730 days is 2 years)
            if pd.to_datetime(non_Min[0].node.extra_info[self.date_key]) - pd.to_datetime(Min_only[0].node.extra_info[self.date_key]) > timedelta(days = 730):
                #if Min nodes are too outdated, take non-Min nodes, otherwise prioritise Min nodes
                return non_Min[: self.top_k_min]
            else:
                return Min_only[: self.top_k_min]
        