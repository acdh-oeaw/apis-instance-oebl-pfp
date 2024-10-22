from rest_framework import renderers
from rdflib import Graph


class BaseRdfRenderer(renderers.BaseRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        result = Graph()

        if isinstance(data, dict) and "results" in data:
            # Handle case where data is a dict with multiple graphs
            for graph in data["results"]:
                if isinstance(graph, Graph):
                    result += graph
        elif isinstance(data, Graph):
            # Handle case where data is a single graph
            result = data
        else:
            raise ValueError(
                "Invalid data format. Expected rdflib Graph or dict with 'results' key containing graphs"
            )
        return result


class CidocTTLRenderer(BaseRdfRenderer):
    format = "Cidoc"
    media_type = "text/ttl"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return (
            super()
            .render(data, accepted_media_type, renderer_context)
            .serialize(format="ttl")
        )


class CidocXMLRenderer(BaseRdfRenderer):
    format = "Cidoc"
    media_type = "application/rdf+xml"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return (
            super()
            .render(data, accepted_media_type, renderer_context)
            .serialize(format="xml")
        )
