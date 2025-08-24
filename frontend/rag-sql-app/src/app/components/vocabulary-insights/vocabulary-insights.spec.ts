import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VocabularyInsights } from './vocabulary-insights';

describe('VocabularyInsights', () => {
  let component: VocabularyInsights;
  let fixture: ComponentFixture<VocabularyInsights>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VocabularyInsights]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VocabularyInsights);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
