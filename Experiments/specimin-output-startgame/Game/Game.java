package Game;

import java.awt.*;
import javax.swing.*;

public class Game {

  public static Game instance;

  public static void startGame(AI ai) throws Exception {
    if (instance == null) {
      instance = new Game(ai);
    }
  }

  private Game(AI ai) throws Exception {
    throw new java.lang.Error();
  }
}
