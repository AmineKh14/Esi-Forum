from django.shortcuts import render, redirect, get_object_or_404
from .models import Publication,Profile,Utilisateur,Commentaire,Report,Message
from django.conf import settings
from datetime import datetime 
from .forms import (
    SignUpForm,userUpdate,
    approveForm,listuserForm,
    deleteForm,addmodForm,adminUpdate,
    UserUpdateForm,ProfileUpdateForm,
    CommentForm)
from django.http import HttpResponse
from django.db.models import Count, F, Q
from django.contrib.auth import login, authenticate,logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.forms.models import model_to_dict
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError


from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DetailView,
    DeleteView
)
import os
def get_current_users():
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_id_list = []
    for session in active_sessions:
        data = session.get_decoded()
        user_id_list.append(data.get('_auth_user_id', None))
    # Query all logged in users based on id list
    return Utilisateur.objects.filter(id__in=user_id_list)

def admin_check(user):
    return user.role=="admin" or user.role=="moderateur"



def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            utilisateur.refresh_from_db()  # load the profile instance created by the signal
            if(form.cleaned_data.get('phone_number')):
                utilisateur.profile.numero_telephone = form.cleaned_data.get('phone_number')
            if(form.cleaned_data.get('promo')):
                utilisateur.profile.promotion = form.cleaned_data.get('promo')
            if(form.cleaned_data.get('bio')):
                utilisateur.profile.bio = form.cleaned_data.get('bio')
            utilisateur.profile.is_appoved =False
            #username = form.cleaned_data.get('username')
            #raw_password = form.cleaned_data.get('password1')
            #user = authenticate(username=username, password=raw_password)
            #login(request, user)
            utilisateur.save()
            return HttpResponse('success')
    else:
        form = SignUpForm()
    return render(request, 'Main/registration.html', {'form': form})


@login_required(login_url='/home/')
@user_passes_test(admin_check,login_url='/home/')
def dashboard(request):
    queryset = get_current_users()
    pubs_populaie=Publication.objects.annotate(num_c_v=(Count('publication')+F('nb_vues'))).order_by('num_c_v')[0:3]
    nbr_user=Utilisateur.objects.all().count()-1
    nbr_topic=Publication.objects.all().count()
    admin_pubs=Publication.objects.filter(auteur__role='admin')
    return render(request, 'Main/admin/Dashboard.html', {"nbr_user":nbr_user,
                                                         "nbr_topic":nbr_topic,
                                                         "pubs_populaie":pubs_populaie,
                                                         "admin_pubs":admin_pubs,
                                                         "nbr_online":queryset.count()
                                                        })

@login_required(login_url='/home/')
@user_passes_test(admin_check,login_url='/home/')
def dashboard_editProfile(request):
    form=adminUpdate()
    add = Profile.objects.filter(user__username=request.user)
    for ad in add:
        admin = ad
    if request.method == 'POST' :
        form = adminUpdate(request.POST)
        
        if form.is_valid(): 
            
            if(form.cleaned_data.get('username1')):
                if(form.cleaned_data.get('username')):
                    Utilisateur.objects.filter(username=form.cleaned_data.get('username1')).update(username=form.cleaned_data.get('username'))
                if(form.cleaned_data.get('email')):
                    Utilisateur.objects.filter(username=form.cleaned_data.get('username1')).update(email=form.cleaned_data.get('email'))
                if(form.cleaned_data.get('firstname')):
                    Utilisateur.objects.filter(username=form.cleaned_data.get('username1')).update(first_name=form.cleaned_data.get('firstname'))
                if(form.cleaned_data.get('lastname')):
                    Utilisateur.objects.filter(username=form.cleaned_data.get('username1')).update(first_name=form.cleaned_data.get('last_name'))
     
    
    return render(request, 'Main/admin/EditUser.html', {"admin":admin,
                                                        "form":form
                                                        })


def logout_request(request):
    logout(request)
    return redirect('home')




def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Logged in successfully as {username}")
                return redirect('home')
            else:
                messages.info(request,"User dosn't exist")
        else:
            messages.info(request,"Invalid Syntaxe")
    form = AuthenticationForm()
    return render(request,"Main/Home-Logged.html", {"form":form})



def loggedin (request):
    return render(request, "Main/Home-Logged.html")


def editeProfile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST,instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES)
        if u_form.is_valid() and p_form.is_valid():
            print("============================================================")
            u_form.save()
            p_form.save(commit=False)
            return HttpResponse('User info changed !')


    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm()

    context ={
        'u_form' : u_form,
        'p_form' : p_form
    }

    return render(request,"Main/usersettings.html",context)


def search(request):
    query =request.GET.get('q')
    essai = Publication.objects.all()
    results = Publication.objects.filter(Q(titre__contains=query))
    context ={
        'essai':essai,
        'resutls':results
    }
    return render(request,"Main/searchresults.html",context)




# Publications

class PostListView(ListView):
    model = Publication
    context_object_name = 'posts'
    template_name = 'Main/Home-Logged.html'
    ordering = ['-date_de_publication']
    paginate_by = 4


class PostDetailView(DetailView):
    model = Publication
    template_name = 'Main/viewPost.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Publication
    template_name = 'Main/Home-Logged.html'
    fields = ['titre', 'content']


    def form_valid(self, form):
        form.instance.auteur = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Publication
    template_name = 'Main/viewPost.html'
    fields = ['titre', 'content']


    def form_valid(self, form):
        form.instance.auteur = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.auteur


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Publication
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.auteur


#Comments

def add_comment_to_post(request, pk):
    post = get_object_or_404(Publication, pk=pk)
    if request.method == "POST":
        #form = CommentForm(request.POST)
        
        comment = Commentaire()
        comment.publication = post
        content = request.POST['content-comment']
        comment.content = content
        comment.commented_by = request.user
        comment.save()
        return redirect('post-detail', pk=post.pk)
    
    return redirect('post-detail', pk=post.pk)

class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Commentaire
    template_name = 'Main/viewPost.html'
    fields = ['titre', 'content']


    def form_valid(self, form):
        form.instance.auteur = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.commented_by


@login_required
def comment_remove(request, pk1,pk2):
    if request.method == "POST":
        comment = get_object_or_404(Commentaire, pk=pk2)
        if comment.commented_by == request.user:
            comment.delete()
            return redirect('post-detail', pk=comment.publication.id)
        else:
            return redirect('post-detail', pk=comment.publication.id)

@login_required
def comment_update(request, pk1,pk2):
    post = get_object_or_404(Publication, pk=pk1)
    if request.method == "POST":
        comment = get_object_or_404(Commentaire, pk=pk2)
        if comment.commented_by == request.user:
            comment.publication = post
            content = request.POST['content-comment']
            comment.content = content
            comment.commented_by = request.user
            comment.save()
            return redirect('post-detail', pk=post.pk)
    
    return redirect('post-detail', pk=post.pk)

    
class ReportListView(ListView):
    template_name = 'Main/admin/MsgsReports.html'
    context_object_name = 'reports_list'
    def get_context_data(self, **kwargs):
        context = super(ReportListView, self).get_context_data(**kwargs)
        context['messages_list'] = Message.objects.all()
        return context
    def get_queryset(self):
        return Report.objects.all()

class ReportDeleteView(DeleteView):
    template_name = 'Main/admin/MsgsReports.html'
    model = Report
    success_url = '/reports/'

class MessageDeleteView(DeleteView):
    template_name = 'Main/admin/MsgsReports.html'
    model = Message
    success_url = '/reports/'


def add_message(request):
    if request.method == "POST":
        message = Message()
        if request.user.is_authenticated:
            email = request.user.email
        else:
            email = request.POST.get('email-message')
        content = request.POST['Message-input']
        message.message = content
        message.sybject = 'Message'
        message.email = email
        message.save()

    return redirect('home')



userroleDashboard='all'
usernameDashboard=''

#@login_required(login_url='/home/')
#@user_passes_test(admin_check,login_url='/home/')
class UsersListView(ListView):
    global usernameDashboard
    template_name = 'Main/admin/Users.html'
    context_object_name = 'users_list'
    def get_context_data(self, **kwargs):
        form = userUpdate()
        formm =addmodForm()
        context = super(UsersListView,self).get_context_data(**kwargs)
        context['users_no_list'] = Utilisateur.objects.filter(profile__is_appoved =False)
        context['users_ban_list'] = Utilisateur.objects.filter(banned =True)
        context['form'] = form
        context['formm'] = formm
        return context
        
    def get_queryset(self):
        print(usernameDashboard)
        user=Utilisateur.objects.filter(profile__is_appoved =True).filter(banned=False)
        if(userroleDashboard!='all'):
            user=user.filter(role =userroleDashboard)
        if(len(usernameDashboard)>1):
            user=Utilisateur.objects.filter(username =usernameDashboard)
            return  user.filter(profile__is_appoved =True)
        else:
            return user



def approverUser(request,pk):
    user=Profile.objects.filter(id=pk).update(is_appoved=True) 
    return redirect('users')
    
def supprimerUser(request,pk):
    Utilisateur.objects.filter(id=pk).delete()
    return redirect('users')

def updateUser(request,pk):   
    user=Utilisateur.objects.get(id=pk)
    if request.method == 'POST':
        try:
            print("okkk")
            img = request.FILES['image']
            img_extension = os.path.splitext(img.name)[1]
            print(img.name)
            print(settings.MEDIA_ROOT)
            user_folder = settings.MEDIA_ROOT+'/profile_pics/'
            print(user_folder)
            if not os.path.exists(user_folder):
                os.mkdir(user_folder)

            img_save_path = user_folder+img.name
            print(img_save_path )

            with open(img_save_path, 'wb+') as f:
                for chunk in img.chunks():
                    f.write(chunk)
        
            user.profile.image= 'profile_pics/'+img.name
            user.save()
        except :
            pass
        user=Utilisateur.objects.filter(id=pk)
        username =request.POST.get('username')
        if username:
            user.update(username=username)
            
        firstname =request.POST.get('firstname')
        if firstname:
            user.update(first_name=firstname)
        
        lastname =request.POST.get('lastname')
        if lastname:
            user.update(lastname=lastname)
        
        email =request.POST.get('email')
        if email:
            user.update(email=email)
         
        role =request.POST.get('role')
        if role:
            user.update(role=role)

        password =request.POST.get('password')
        if password:
            user.update(password=password)
        
               
        
           

    return redirect('users')


def searchUser(request):
    global usernameDashboard
    if request.POST:
        usernameDashboard= request.POST['username']
        print(usernameDashboard)
    return redirect('users')

def selectrole(request):
    global userroleDashboard
    role=request.GET['role']
    userroleDashboard=role;
    print(userroleDashboard)
    return redirect('users')

def addmod(request):   

    if request.method == 'POST':
        user=Utilisateur()
        password =request.POST.get('password')
        password1 =request.POST.get('password1')

        if password:
            if password==password1:
                username =request.POST.get('username')
                if username:
                    user.username=username
            
                firstname =request.POST.get('firstname')
                if firstname:
                    user.first_name=firstname
        
                lastname =request.POST.get('lastname')
                if lastname:
                    user.lastname=lastname
        
                email =request.POST.get('email')
                if email:
                    user.email=email
         
                role =request.POST.get('role')
                if role:
                    user.role=role
                user.save()

        
    
        try:
            print("okkk")
            img = request.FILES['image']
            img_extension = os.path.splitext(img.name)[1]
            print(img.name)
            print(settings.MEDIA_ROOT)
            user_folder = settings.MEDIA_ROOT+'/profile_pics/'
            print(user_folder)
            if not os.path.exists(user_folder):
                os.mkdir(user_folder)

            img_save_path = user_folder+img.name
            print(img_save_path )

            with open(img_save_path, 'wb+') as f:
                for chunk in img.chunks():
                    f.write(chunk)
        
            user.profile.image= 'profile_pics/'+img.name
            user.save()
        except :
            pass

                 
    return redirect('users')

def unban(request,pk):   
    user=Utilisateur.objects.filter(id=pk)
    for us in user:
        us.banned=False
        us.mod=None
        us.subject=None
        us.date=None
        us.duree=0
        us.save()

    return redirect('users')

def ban(request,pk):   
    user=Utilisateur.objects.filter(id=pk)
    if request.method == 'POST':
        reason =request.POST['reason']
        duree =request.POST['duree']
        for us in user:
            us.banned=True
            us.mod=request.user
            us.subject=reason
            us.date=datetime.now()
            us.duree=duree
            us.save()

    return redirect('users')