<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Navbar Bootstrap avec sections masquées</title>

  <!-- Bootstrap 5 -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

  <style>
    html {
      scroll-behavior: smooth;
    }
    section {
      padding: 100px 0;
      min-height: 100vh;
      display: none; /* toutes cachées par défaut */
    }
    section.active {
      display: block; /* seule la section active est visible */
    }
  </style>
</head>
<body>

  <!-- Navbar -->
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
    <div class="container justify-content-center">
      <a class="navbar-brand me-4" href="#">MonSite</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse justify-content-center" id="navbarNav">
        <ul class="navbar-nav">
          <li class="nav-item"><a class="nav-link active" href="#accueil">Accueil</a></li>
          <li class="nav-item"><a class="nav-link" href="#services">Services</a></li>
          <li class="nav-item"><a class="nav-link" href="#projets">Projets</a></li>
          <li class="nav-item"><a class="nav-link" href="#contact">Contact</a></li>
        </ul>
      </div>
    </div>
  </nav>

  <!-- Sections -->
  <section id="accueil" class="bg-light text-center active">
    <div class="container">
      <h1 class="display-4">Bienvenue</h1>
      <p class="lead">Ceci est la section d'accueil.</p>
    </div>
  </section>

  <section id="services" class="bg-white text-center">
    <div class="container">
      <h2>Nos Services</h2>
      <p>Découvrez ce que nous offrons à nos clients.</p>
    </div>
  </section>

  <section id="projets" class="bg-light text-center">
    <div class="container">
      <h2>Projets</h2>
      <p>Voici quelques exemples de nos réalisations.</p>
    </div>
  </section>

  <section id="contact" class="bg-white text-center">
    <div class="container">
      <h2>Contact</h2>
      <p>Entrons en contact pour discuter de vos besoins.</p>
    </div>
  </section>

  <!-- Script Bootstrap + JS -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

  <script>
    // Gestion de l'affichage des sections
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section');

    navLinks.forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault();

        // Supprime l'état actif de tous les liens
        navLinks.forEach(l => l.classList.remove('active'));

        // Cache toutes les sections
        sections.forEach(s => s.classList.remove('active'));

        // Active le lien et la section correspondante
        link.classList.add('active');
        const target = document.querySelector(link.getAttribute('href'));
        if (target) target.classList.add('active');
      });
    });
  </script>
</body>
</html>