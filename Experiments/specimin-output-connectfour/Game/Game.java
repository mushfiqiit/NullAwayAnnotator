package Game;

import java.awt.*;
import javax.swing.*;

public class Game {

  private static final int[][] board = null;

  public int checkWinner() {
    for (int i = 0; i < 7; i++) {
      for (int j = 0; j < 6; j++) {
        if (j < 3) {
          if (board[i][j] == board[i][j + 1]
              && board[i][j] == board[i][j + 2]
              && board[i][j] == board[i][j + 3]
              && board[i][j] != 0) return board[i][j];
        }
        if (i < 4) {
          if (board[i][j] == board[i + 1][j]
              && board[i][j] == board[i + 2][j]
              && board[i][j] == board[i + 3][j]
              && board[i][j] != 0) return board[i][j];
        }
        if (i < 4 && j < 3) {
          if (board[i][j] == board[i + 1][j + 1]
              && board[i][j] == board[i + 2][j + 2]
              && board[i][j] == board[i + 3][j + 3]
              && board[i][j] != 0) return board[i][j];
        }
        if (i > 2 && j < 3) {
          if (board[i][j] == board[i - 1][j + 1]
              && board[i][j] == board[i - 2][j + 2]
              && board[i][j] == board[i - 3][j + 3]
              && board[i][j] != 0) return board[i][j];
        }
      }
    }
    return 0;
  }
}
