from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.forms.models import modelformset_factory
from django.shortcuts import redirect, render_to_response
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView,
)

from .forms import SubscriptionCreationForm
from .formsets import SubscriptionModelFormset
from .models import (
    Product,
    Subscription,
)


class BaseListAndCreateView(ListView):
    """
    Abstract base view for ProductListAndCreationView and
    EmailNotificationListAndCreateView as do nearly the same underneath
    """

    def __init__(self, *args, **kwargs):
        """
        Overwritten init method sets list model as model for ListView
        :param args: positional arguments
        :param kwargs: keyword arguments
        :type args: List
        :type kwargs: Dict
        """
        self.model = self.list_model

        super(BaseListAndCreateView, self).__init__(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """
        Extends base context with formular context
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: updated context with formular data
        :type args: List
        :type kwargs: Dict
        :rtype: Dict
        """
        context = super(BaseListAndCreateView, self).get_context_data(*args, **kwargs)
        creation_formset_class = modelformset_factory(model=self.create_model, formset=self.create_formset, form=self.create_form)
        if self.request.method == 'POST':
            post = self.request.POST.copy()
            for i in range(int(self.request.POST.get('form-TOTAL_FORMS', 1000))):
                post.update({'form-%s-owner' % i: self.request.user.id})
            creation_formset = creation_formset_class(self.request.user, post)
        else:
            creation_formset = creation_formset_class(user=self.request.user, queryset=QuerySet(model=self.model).none())
        context['creation_formset'] = creation_formset
        return context

    def post(self, request, *args, **kwargs):
        """
        Represents the post view. Redirects to monitor_view if form is valid,
        else renders form with errors
        :param request: Incoming HttpRequest
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: HttpResponse object
        :type request: HttpRequest
        :type args: List
        :type kwargs: Dict
        :rtype: HttpResponse
        """
        parent_view = super(BaseListAndCreateView, self).get(request, *args, **kwargs)
        creation_formset = parent_view.context_data['creation_formset']
        if creation_formset.is_valid():
            creation_formset.save()
            return redirect('monitor_view')
        return parent_view

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """
        Overwritting this method the make every instance of the view
        login_required
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: Result of super method. As this dispatches the handling method
        for the incoming request and calls it, the return is a HttpResponse
        object
        :type args: List
        :type kwargs: Dict
        :rtype: HttpResponse
        """
        return super(BaseListAndCreateView, self).dispatch(*args, **kwargs)


class ProductListAndCreateView(BaseListAndCreateView):
    list_model = Product
    create_model = Subscription
    create_form = SubscriptionCreationForm
    create_formset = SubscriptionModelFormset

    template_name = 'price_monitor/product_list_and_create.html'
    template_name_suffix = ''

    def get_queryset(self):
        qs = super(ProductListAndCreateView, self).get_queryset()
        return qs.filter(subscription__owner=self.request.user.pk)


@login_required
def charts_demo_view(request):
    """
    Demo view for displaying charts.
    :param request: the incoming request
    :return: the final response
    :type request: HttpRequest
    :rtype: HttpResponse
    """
    return render_to_response(
        'price_monitor/charts_demo.html',
        {
            'products': Product.objects.all().order_by('?')[0:20],
        }
    )
