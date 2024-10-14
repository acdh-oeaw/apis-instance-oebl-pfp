from rest_framework import renderers
from rdflib import Graph


class BaseRdfRenderer(renderers.BaseRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        result = Graph()

        if isinstance(data, dict) and "results" in data:
            # Handle case where data is a dict with multiple graphs
            for graph in data["results"]:
                if isinstance(graph, Graph):
                    # Merge triples
                    for triple in graph:
                        result.add(triple)
                    # Merge namespace bindings
                    for prefix, namespace in graph.namespaces():
                        result.bind(prefix, namespace, override=False)
        elif isinstance(data, Graph):
            # Handle case where data is a single graph
            result = data
            # Ensure namespaces are properly bound in the single graph case
            for prefix, namespace in data.namespaces():
                result.bind(prefix, namespace, override=False)
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
