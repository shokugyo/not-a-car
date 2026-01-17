import { useTripStore } from '../../store';
import { DestinationSearch } from './DestinationSearch';
import { RoutePlanView } from './RoutePlanView';
import { TripConfirmation } from './TripConfirmation';
import { VehicleSelection } from './VehicleSelection';
import { TripComplete } from './TripComplete';

export function TripPlannerSheet() {
  const { currentStep } = useTripStore();

  return (
    <div className="min-h-[200px]">
      {currentStep === 'search' && <DestinationSearch />}
      {currentStep === 'plan' && <RoutePlanView />}
      {currentStep === 'confirm' && <TripConfirmation />}
      {currentStep === 'vehicle' && <VehicleSelection />}
      {currentStep === 'complete' && <TripComplete />}
    </div>
  );
}
