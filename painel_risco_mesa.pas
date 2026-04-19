// ============================================================
//  PAINEL DE RISCO - MESA PROPRIETÁRIA
//  Autor  : Mesa Proprietária
//  Versão : 1.0
//
//  Finalidade:
//    Exibe um painel visual com o status da conta, o risco
//    restante, sugestão de lotes e meta mínima de recuperação.
//
//  Como usar:
//    Ajuste os inputs com os valores reais da sua conta antes
//    de abrir o pregão. O painel atualiza a cada barra.
//
//  Referência WIN:
//    1 ponto = R$ 0,20 por contrato mini índice
// ============================================================

input
  MargemTotal      (3000.00);   // Margem disponibilizada pela mesa (R$)
  ResultadoAtual   (-2500.00);  // Resultado atual do dia (negativo = prejuízo)
  MargemPorContrato(100.00);    // Margem exigida por contrato (R$)
  LimitePerda      (0.90);      // % da margem = limite de stop da mesa
  MetaDiaria       (500.00);    // Meta de ganho diário (R$)
  ValorPonto       (0.20);      // Valor de 1 ponto por contrato (WIN = 0.20)

var
  SaldoRestante     : Float;
  LimiteAbsoluto    : Float;
  PercentualUsado   : Float;
  PrejuizoAbsoluto  : Float;
  ContratosPermitidos: Integer;
  PontosParaRecuperar: Float;
  PontosParaMeta    : Float;
  CorStatus         : Integer;
  CorBarra          : Integer;
  Linha             : String;

begin
  // --- Cálculos principais ---
  PrejuizoAbsoluto    := Abs(ResultadoAtual);
  LimiteAbsoluto      := MargemTotal * LimitePerda;        // Limite de loss em R$
  SaldoRestante       := MargemTotal - PrejuizoAbsoluto;   // Margem que sobra
  PercentualUsado     := (PrejuizoAbsoluto / LimiteAbsoluto) * 100;

  // Quantos contratos ainda posso operar com o saldo restante
  if SaldoRestante > 0 then
    ContratosPermitidos := Trunc(SaldoRestante / MargemPorContrato)
  else
    ContratosPermitidos := 0;

  // Pontos necessários para recuperar o prejuízo com os contratos restantes
  if (ContratosPermitidos > 0) and (ValorPonto > 0) then
    PontosParaRecuperar := PrejuizoAbsoluto / (ValorPonto * ContratosPermitidos)
  else
    PontosParaRecuperar := 0;

  // Pontos necessários para atingir a meta do dia (recuperar + lucrar)
  if (ContratosPermitidos > 0) and (ValorPonto > 0) then
    PontosParaMeta := (PrejuizoAbsoluto + MetaDiaria) / (ValorPonto * ContratosPermitidos)
  else
    PontosParaMeta := 0;

  // --- Definição de cor de status ---
  // Verde = seguro, Amarelo = atenção, Laranja = crítico, Vermelho = emergência
  if PercentualUsado < 50 then
    CorStatus := clLime
  else if PercentualUsado < 75 then
    CorStatus := clYellow
  else if PercentualUsado < 90 then
    CorStatus := clOrange
  else
    CorStatus := clRed;

  // --- Painel visual via Plot com labels ---
  // Linha 1 - Separador
  SetPlotColor(1, CorStatus);
  SetPlotWidth(1, 3);
  Plot(Close); // Plot invisível só para ativar o indicador

  // --- Exibição de texto no gráfico ---
  // (Use os campos de texto do indicador para exibir os valores abaixo)

  // Plot 2 - Nível de saldo restante como linha horizontal
  SetPlotColor(2, CorStatus);
  SetPlotWidth(2, 2);
  SetPlotStyle(2, psDash);
  Plot2(Close); // placeholder

  // --- Coloração das barras pelo nível de risco ---
  if PercentualUsado >= 90 then
    PaintBar(clRed)       // Emergência - quase no limite
  else if PercentualUsado >= 75 then
    PaintBar(clOrange)    // Crítico
  else if PercentualUsado >= 50 then
    PaintBar(clYellow);   // Atenção

  // ============================================================
  //  VALORES CALCULADOS (visualize no painel de variáveis)
  //
  //  Acesse: Ferramentas > Painel de Variáveis do Indicador
  //
  //  SaldoRestante      = Margem que ainda resta (R$)
  //  PercentualUsado    = % do limite de perda já consumido
  //  ContratosPermitidos= Contratos que ainda pode operar
  //  PontosParaRecuperar= Pontos p/ zerar o prejuízo
  //  PontosParaMeta     = Pontos p/ zerar E atingir a meta
  // ============================================================

  // Plots numéricos para leitura no painel lateral
  Plot3(SaldoRestante);          // Saldo restante em R$
  Plot4(PercentualUsado);        // % do limite usado
  Plot5(ContratosPermitidos);    // Contratos permitidos
  Plot6(PontosParaRecuperar);    // Pontos para recuperar
  Plot7(PontosParaMeta);         // Pontos para atingir a meta

end;

// ============================================================
//  LEGENDA DOS PLOTS:
//    Plot 1  = Referência (linha de preço)
//    Plot 2  = Referência (linha de preço)
//    Plot 3  = Saldo Restante (R$)
//    Plot 4  = % Limite Usado
//    Plot 5  = Contratos Permitidos
//    Plot 6  = Pontos para Recuperar
//    Plot 7  = Pontos para Meta
//
//  COLORAÇÃO DE BARRAS:
//    Normal  = Risco < 50%  (seguro)
//    Amarelo = Risco 50-74% (atenção)
//    Laranja = Risco 75-89% (crítico)
//    Vermelho= Risco >= 90% (emergência - pare de operar!)
// ============================================================
