labels_delais.forEach(m => {
  if (!(m in delais_json)) {
    console.warn("Clé manquante dans delais_json :", m);
  }
});