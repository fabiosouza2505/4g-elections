# ============================================================================
# DOWNLOAD PIB MUNICIPAL VIA sidrar (PACOTE R)
# ============================================================================
# Execute este script em seu computador local onde você tem acesso à internet
# sem restrições de proxy

install.packages("sidrar")
library(tidyverse)
library(sidrar)

# Configurações
TABELA <- 5938
OUTPUT_FILE <- "pib_municipal_2010_2022.csv"

cat("\n", strrep("=", 80), "\n")
cat("DOWNLOAD PIB MUNICIPAL - SIDRA/IBGE\n")
cat(strrep("=", 80), "\n\n")

# ============================================================================
# ESTRATÉGIA 1: BAIXAR TUDO DE UMA VEZ (SE POSSÍVEL)
# ============================================================================

cat("🎯 ESTRATÉGIA 1: Download completo\n\n")

tryCatch({
  
  pib_completo <- get_sidra(
    x = TABELA,
    variable = c(37, 513),  # PIB corrente e per capita
    period = "2010-2022",
    geo = "City"
  )
  
  cat("✅ Download completo bem-sucedido!\n")
  cat(sprintf("📊 Total de linhas: %s\n", nrow(pib_completo)))
  
  # Salvar
  write_csv(pib_completo, OUTPUT_FILE)
  cat(sprintf("💾 Arquivo salvo: %s\n", OUTPUT_FILE))
  
}, error = function(e) {
  
  cat("❌ Estratégia 1 falhou:", conditionMessage(e), "\n\n")
  
  # =========================================================================
  # ESTRATÉGIA 2: BAIXAR ANO POR ANO
  # =========================================================================
  
  cat("🎯 ESTRATÉGIA 2: Download ano por ano\n\n")
  
  anos <- 2010:2022
  resultados <- list()
  
  for(i in seq_along(anos)) {
    ano <- anos[i]
    cat(sprintf("📅 Ano %d (%d/%d)... ", ano, i, length(anos)), flush = TRUE)
    
    tryCatch({
      df <- get_sidra(
        x = TABELA,
        variable = c(37, 513),
        period = as.character(ano),
        geo = "City"
      )
      
      resultados[[as.character(ano)]] <- df
      cat(sprintf("✅ %s linhas\n", nrow(df)))
      
      Sys.sleep(2)  # Delay para não sobrecarregar
      
    }, error = function(e2) {
      cat("❌ ERRO\n")
    })
  }
  
  # Combinar resultados
  if(length(resultados) > 0) {
    pib_completo <- bind_rows(resultados)
    
    write_csv(pib_completo, OUTPUT_FILE)
    
    cat("\n", strrep("=", 80), "\n")
    cat("✅ DOWNLOAD CONCLUÍDO\n")
    cat(strrep("=", 80), "\n\n")
    cat(sprintf("📊 Total de linhas: %s\n", nrow(pib_completo)))
    cat(sprintf("📋 Anos: %s a %s\n", min(pib_completo$Ano), max(pib_completo$Ano)))
    cat(sprintf("🏙️  Municípios: %s\n", n_distinct(pib_completo$`Município (Código)`)))
    cat(sprintf("💾 Arquivo: %s\n\n", OUTPUT_FILE))
  }
})

cat(strrep("=", 80), "\n\n")