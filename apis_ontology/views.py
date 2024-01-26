from apis_core.generic.views import List

from .models import Person


class PersonList(List):
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.model = Person
        self.queryset = self.model.objects.all()
