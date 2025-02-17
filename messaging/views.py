# messages/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.views import View
from django.views.generic import CreateView, ListView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from .models import Message
from .forms import MessageForm, ReplyMessageForm


# 1. CreateMessageView: For sending a message
class CreateMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'messaging/message_form.html'
    success_url = reverse_lazy('sent_messages')
    permission_required = 'messages.add_message'

    def get_initial(self):
        initial = super().get_initial()
        recipient_id = self.request.GET.get('recipient', None)
        if recipient_id:
            initial['recipient'] = recipient_id  # The form field name is 'recipient'
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.sender = self.request.user
        return super().form_valid(form)


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'messaging/message_detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        qs = super().get_queryset()
        # Allow access if the current user is either the recipient or the sender.
        return qs.filter(Q(recipient=self.request.user) | Q(sender=self.request.user))

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        message = self.object
        # Mark as read only if the current user is the recipient and it's unread.
        if message.recipient == request.user and not message.is_read:
            message.is_read = True
            message.save()
        return response


class ReplyMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = ReplyMessageForm
    template_name = 'messaging/reply_message.html'
    success_url = reverse_lazy('inbox')

    def get(self, request, *args, **kwargs):
        # Retrieve the original message when handling GET requests.
        self.original_message = get_object_or_404(
            Message, pk=kwargs.get('pk'), recipient=request.user
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Retrieve the original message when handling POST requests.
        self.original_message = get_object_or_404(
            Message, pk=kwargs.get('pk'), recipient=request.user
        )
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['subject'] = f"Re: {self.original_message.subject}"
        return initial

    def form_valid(self, form):
        reply = form.save(commit=False)
        reply.sender = self.request.user
        reply.recipient = self.original_message.sender
        reply.save()
        self.object = reply  # Set self.object so get_success_url() can access it
        messages.success(self.request, "Your reply has been sent.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['original_message'] = self.original_message
        return context


# 2. InboxView: For listing received messages
class InboxView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'messaging/inbox.html'
    context_object_name = 'messages'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(recipient=self.request.user, is_archived=False)
        query = self.request.GET.get('q', '')
        if query:
            qs = qs.filter(subject__icontains=query) | qs.filter(sender__username__icontains=query)
        return qs.order_by('-timestamp')


# 3. SentMessagesView: For listing messages sent by the user
class SentMessagesView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'messaging/sent_messages.html'
    context_object_name = 'messages'

    def get_queryset(self):
        # Filter messages where the current user is the sender, ordered by timestamp descending
        queryset = Message.objects.filter(sender=self.request.user).order_by('-timestamp')
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(subject__icontains=query)
        return queryset


# 4. Archive Message: Function-based view to archive a message
class ArchiveMessageView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        # Retrieve the message ensuring that the current user is the recipient.
        message = get_object_or_404(Message, pk=pk, recipient=request.user)
        message.is_archived = True
        message.save()
        return redirect('inbox')
